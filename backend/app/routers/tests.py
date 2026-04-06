from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_teacher
from app.models import ClassRoom, TestPaper, TestQuestion, TestResult, TestRun, User
from app.schemas.test import (
    TestPaperCreateRequest,
    TestPaperResponse,
    TestQuestionCreateRequest,
    TestQuestionResponse,
    TestQuestionUpdateRequest,
    TestResultItem,
    TestRunResponse,
)
from app.services.test_service import TestService

router = APIRouter(prefix="/tests", tags=["tests"])
test_service = TestService()


async def _get_teacher_paper(db: AsyncSession, paper_id: int, teacher_id: int) -> TestPaper:
    result = await db.execute(select(TestPaper).where(TestPaper.id == paper_id, TestPaper.teacher_id == teacher_id))
    paper = result.scalar_one_or_none()
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")
    return paper


@router.post("/papers", response_model=TestPaperResponse)
async def create_paper(
    payload: TestPaperCreateRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> TestPaperResponse:
    class_result = await db.execute(
        select(ClassRoom).where(ClassRoom.id == payload.class_id, ClassRoom.teacher_id == teacher.id)
    )
    if class_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    paper = TestPaper(class_id=payload.class_id, teacher_id=teacher.id, title=payload.title)
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return TestPaperResponse(
        id=paper.id,
        class_id=paper.class_id,
        teacher_id=paper.teacher_id,
        title=paper.title,
        created_at=paper.created_at,
        questions=[],
    )


@router.get("/papers", response_model=list[TestPaperResponse])
async def list_papers(
    class_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> list[TestPaperResponse]:
    stmt = (
        select(TestPaper)
        .options(selectinload(TestPaper.questions))
        .where(TestPaper.teacher_id == teacher.id)
        .order_by(TestPaper.created_at.desc())
    )
    if class_id is not None:
        stmt = stmt.where(TestPaper.class_id == class_id)
    result = await db.execute(stmt)
    return [TestPaperResponse.model_validate(paper) for paper in result.scalars().all()]


@router.post("/papers/{paper_id}/questions", response_model=TestQuestionResponse)
async def add_question(
    paper_id: int,
    payload: TestQuestionCreateRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> TestQuestionResponse:
    await _get_teacher_paper(db, paper_id, teacher.id)
    question = TestQuestion(paper_id=paper_id, **payload.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return TestQuestionResponse.model_validate(question)


@router.put("/questions/{question_id}", response_model=TestQuestionResponse)
async def update_question(
    question_id: int,
    payload: TestQuestionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> TestQuestionResponse:
    question = await db.get(TestQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    await _get_teacher_paper(db, question.paper_id, teacher.id)
    for key, value in payload.model_dump().items():
        setattr(question, key, value)
    await db.commit()
    await db.refresh(question)
    return TestQuestionResponse.model_validate(question)


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> dict:
    question = await db.get(TestQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    await _get_teacher_paper(db, question.paper_id, teacher.id)
    await db.delete(question)
    await db.commit()
    return {"message": "Question deleted."}


@router.post("/papers/{paper_id}/execute", response_model=TestRunResponse)
async def execute_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> TestRunResponse:
    paper = await _get_teacher_paper(db, paper_id, teacher.id)
    run = await test_service.queue_run(db, paper)
    await db.commit()
    await db.refresh(run)
    return TestRunResponse.model_validate(run)


@router.get("/runs/{run_id}", response_model=TestRunResponse)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> TestRunResponse:
    result = await db.execute(
        select(TestRun).join(TestPaper, TestPaper.id == TestRun.paper_id).where(TestRun.id == run_id, TestPaper.teacher_id == teacher.id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return TestRunResponse.model_validate(run)


@router.get("/papers/{paper_id}/results", response_model=list[TestResultItem])
async def get_results(
    paper_id: int,
    run_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> list[TestResultItem]:
    await _get_teacher_paper(db, paper_id, teacher.id)
    if run_id is None:
        latest_run_result = await db.execute(
            select(TestRun).where(TestRun.paper_id == paper_id).order_by(TestRun.created_at.desc()).limit(1)
        )
        latest_run = latest_run_result.scalar_one_or_none()
        if latest_run:
            run_id = latest_run.id
    stmt = (
        select(TestResult, User)
        .join(User, User.id == TestResult.student_id)
        .where(TestResult.paper_id == paper_id)
        .order_by(User.display_name.asc())
    )
    if run_id is not None:
        stmt = stmt.where(TestResult.run_id == run_id)
    rows = await db.execute(stmt)
    return [
        TestResultItem(
            student_id=user.id,
            student_name=user.display_name,
            score=result.score,
            total=result.total,
            detail=result.detail,
            tested_at=result.tested_at,
        )
        for result, user in rows.all()
    ]
