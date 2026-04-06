from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_teacher
from app.models import AIKnowledge, ChatMessage, ChatSession, ClassRoom, ClassStudent, KnowledgeChangeLog, TestPaper, TestResult, User
from app.schemas.analytics import ClassOverviewResponse, StudentAnalyticsItem, StudentProgressResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/analytics", tags=["analytics"])
knowledge_service = KnowledgeService()


async def _teacher_owns_class(db: AsyncSession, class_id: int, teacher_id: int) -> ClassRoom:
    result = await db.execute(select(ClassRoom).where(ClassRoom.id == class_id, ClassRoom.teacher_id == teacher_id))
    classroom = result.scalar_one_or_none()
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    return classroom


@router.get("/class/{class_id}/overview", response_model=ClassOverviewResponse)
async def class_overview(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> ClassOverviewResponse:
    await _teacher_owns_class(db, class_id, teacher.id)
    students_result = await db.execute(select(ClassStudent).where(ClassStudent.class_id == class_id))
    students = list(students_result.scalars().all())
    knowledge_result = await db.execute(select(AIKnowledge).where(AIKnowledge.class_id == class_id))
    knowledge_records = list(knowledge_result.scalars().all())
    topic_coverage = defaultdict(int)
    for record in knowledge_records:
        for topic, payload in record.knowledge_data.get("topics", {}).items():
            if payload.get("knowledge") or payload.get("examples"):
                topic_coverage[topic] += 1
    average_knowledge_items = 0.0
    if knowledge_records:
        average_knowledge_items = sum(knowledge_service.count_items(record.knowledge_data) for record in knowledge_records) / len(knowledge_records)
    latest_tests_result = await db.execute(
        select(TestResult).join(User, User.id == TestResult.student_id).join(ClassStudent, ClassStudent.student_id == User.id).where(ClassStudent.class_id == class_id)
    )
    test_results = list(latest_tests_result.scalars().all())
    latest_test_average = None
    if test_results:
        latest_test_average = sum(item.score for item in test_results) / len(test_results)
    return ClassOverviewResponse(
        class_id=class_id,
        student_count=len(students),
        topic_coverage=dict(topic_coverage),
        average_knowledge_items=round(average_knowledge_items, 2),
        latest_test_average=round(latest_test_average, 2) if latest_test_average is not None else None,
    )


@router.get("/class/{class_id}/students", response_model=list[StudentAnalyticsItem])
async def class_students(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> list[StudentAnalyticsItem]:
    await _teacher_owns_class(db, class_id, teacher.id)
    student_result = await db.execute(
        select(User)
        .join(ClassStudent, ClassStudent.student_id == User.id)
        .where(ClassStudent.class_id == class_id)
        .order_by(User.display_name.asc())
    )
    students = list(student_result.scalars().all())
    knowledge_result = await db.execute(select(AIKnowledge).where(AIKnowledge.class_id == class_id))
    knowledge_map = {record.student_id: record for record in knowledge_result.scalars().all()}

    payload = []
    for student in students:
        knowledge = knowledge_map.get(student.id)
        latest_result_query = await db.execute(
            select(TestResult)
            .join(TestPaper, TestPaper.id == TestResult.paper_id)
            .where(TestResult.student_id == student.id, TestPaper.class_id == class_id)
            .order_by(TestResult.tested_at.desc())
            .limit(1)
        )
        latest_result = latest_result_query.scalar_one_or_none()
        corrections_result = await db.execute(
            select(func.count(KnowledgeChangeLog.id))
            .join(AIKnowledge, AIKnowledge.id == KnowledgeChangeLog.knowledge_id)
            .where(AIKnowledge.student_id == student.id, AIKnowledge.class_id == class_id)
        )
        corrections = corrections_result.scalar_one()
        payload.append(
            StudentAnalyticsItem(
                student_id=student.id,
                student_name=student.display_name,
                knowledge_items=knowledge_service.count_items(knowledge.knowledge_data if knowledge else {}),
                latest_score=latest_result.score if latest_result else None,
                latest_total=latest_result.total if latest_result else None,
                corrections=corrections,
            )
        )
    return payload


@router.get("/student/{student_id}/progress", response_model=StudentProgressResponse)
async def student_progress(
    student_id: int,
    class_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> StudentProgressResponse:
    await _teacher_owns_class(db, class_id, teacher.id)
    knowledge_result = await db.execute(
        select(AIKnowledge).where(AIKnowledge.student_id == student_id, AIKnowledge.class_id == class_id)
    )
    knowledge = knowledge_result.scalar_one_or_none()
    change_result = await db.execute(
        select(KnowledgeChangeLog)
        .join(AIKnowledge, AIKnowledge.id == KnowledgeChangeLog.knowledge_id)
        .where(AIKnowledge.student_id == student_id, AIKnowledge.class_id == class_id)
        .order_by(KnowledgeChangeLog.created_at.asc())
    )
    changes = list(change_result.scalars().all())
    timeline = [
        {
            "time": change.created_at,
            "action": change.action,
            "item_type": change.item_type,
            "source": change.source,
        }
        for change in changes
    ]
    tests_result = await db.execute(
        select(TestResult)
        .join(TestPaper, TestPaper.id == TestResult.paper_id)
        .where(TestResult.student_id == student_id, TestPaper.class_id == class_id)
        .order_by(TestResult.tested_at.asc())
    )
    tests = [
        {
            "tested_at": result.tested_at,
            "score": result.score,
            "total": result.total,
        }
        for result in tests_result.scalars().all()
    ]
    return StudentProgressResponse(student_id=student_id, class_id=class_id, timeline=timeline, tests=tests)


@router.get("/class/{class_id}/students/{student_id}")
async def student_detail(
    class_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> dict:
    await _teacher_owns_class(db, class_id, teacher.id)
    student_result = await db.execute(select(User).where(User.id == student_id))
    student_user = student_result.scalar_one_or_none()
    knowledge_result = await db.execute(
        select(AIKnowledge).where(AIKnowledge.class_id == class_id, AIKnowledge.student_id == student_id)
    )
    knowledge = knowledge_result.scalar_one_or_none()
    sessions_result = await db.execute(
        select(ChatSession).where(ChatSession.class_id == class_id, ChatSession.student_id == student_id).order_by(ChatSession.updated_at.desc())
    )
    sessions = list(sessions_result.scalars().all())
    session_ids = [session.id for session in sessions]
    messages = []
    if session_ids:
        message_rows = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id.in_(session_ids)).order_by(ChatMessage.created_at.asc())
        )
        messages = [
            {
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content,
                "meta": message.meta,
                "created_at": message.created_at,
            }
            for message in message_rows.scalars().all()
        ]
    return {
        "student_id": student_id,
        "student_name": student_user.display_name if student_user else None,
        "knowledge": knowledge.knowledge_data if knowledge else None,
        "sessions": [
            {
                "id": session.id,
                "type": session.session_type,
                "title": session.title,
                "updated_at": session.updated_at,
            }
            for session in sessions
        ],
        "messages": messages,
    }
