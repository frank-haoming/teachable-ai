from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIKnowledge, ClassStudent, TestPaper, TestQuestion, TestResult, TestRun, User
from app.services.ai_service import AIService
from app.services.knowledge_service import KnowledgeService
from app.utils.constants import (
    RUN_STATUS_COMPLETED,
    RUN_STATUS_FAILED,
    RUN_STATUS_IN_PROGRESS,
    RUN_STATUS_QUEUED,
)


class TestService:
    def __init__(self, ai_service: AIService | None = None, knowledge_service: KnowledgeService | None = None) -> None:
        self.ai_service = ai_service or AIService.build()
        self.knowledge_service = knowledge_service or KnowledgeService(ai_service=self.ai_service)

    async def queue_run(self, db: AsyncSession, paper: TestPaper) -> TestRun:
        student_count_result = await db.execute(
            select(ClassStudent).where(ClassStudent.class_id == paper.class_id)
        )
        students = list(student_count_result.scalars().all())
        run = TestRun(
            paper_id=paper.id,
            class_id=paper.class_id,
            status=RUN_STATUS_QUEUED,
            progress_total=len(students),
            progress_completed=0,
        )
        db.add(run)
        await db.flush()
        return run

    async def claim_next_run(self, db: AsyncSession) -> TestRun | None:
        result = await db.execute(
            select(TestRun).where(TestRun.status == RUN_STATUS_QUEUED).order_by(TestRun.created_at.asc()).limit(1)
        )
        run = result.scalar_one_or_none()
        if run is None:
            return None
        run.status = RUN_STATUS_IN_PROGRESS
        run.started_at = datetime.now(timezone.utc)
        await db.flush()
        return run

    async def execute_run(self, db: AsyncSession, run: TestRun) -> None:
        try:
            paper_result = await db.execute(select(TestPaper).where(TestPaper.id == run.paper_id))
            paper = paper_result.scalar_one()
            questions_result = await db.execute(
                select(TestQuestion).where(TestQuestion.paper_id == paper.id).order_by(TestQuestion.sort_order.asc())
            )
            questions = list(questions_result.scalars().all())
            students_result = await db.execute(
                select(User)
                .join(ClassStudent, ClassStudent.student_id == User.id)
                .where(ClassStudent.class_id == run.class_id)
                .order_by(User.display_name.asc())
            )
            students = list(students_result.scalars().all())
            run.progress_total = len(students)
            await db.execute(delete(TestResult).where(TestResult.run_id == run.id))
            await db.flush()

            for index, student in enumerate(students, start=1):
                knowledge_result = await db.execute(
                    select(AIKnowledge).where(AIKnowledge.student_id == student.id, AIKnowledge.class_id == run.class_id)
                )
                knowledge = knowledge_result.scalar_one_or_none()
                flat = self.knowledge_service.flatten_knowledge(knowledge.knowledge_data if knowledge else {})
                detail_items = []
                score = 0
                for question in questions:
                    options = {
                        "A": question.option_a,
                        "B": question.option_b,
                        "C": question.option_c,
                        "D": question.option_d,
                    }
                    answer = await self.ai_service.answer_question(flat, question.question_text, options=options)
                    is_correct = answer["answer"] == question.correct_answer
                    if is_correct:
                        score += 1
                    detail_items.append(
                        {
                            "question_id": question.id,
                            "question_text": question.question_text,
                            "options": options,
                            "correct_answer": question.correct_answer,
                            "ai_answer": answer["answer"],
                            "reasoning": answer["reasoning"],
                            "is_correct": is_correct,
                        }
                    )
                db.add(
                    TestResult(
                        paper_id=paper.id,
                        student_id=student.id,
                        run_id=run.id,
                        score=score,
                        total=len(questions),
                        detail={"items": detail_items},
                    )
                )
                run.progress_completed = index
                await db.flush()

            run.status = RUN_STATUS_COMPLETED
            run.finished_at = datetime.now(timezone.utc)
            await db.flush()
        except Exception as exc:  # noqa: BLE001
            run.status = RUN_STATUS_FAILED
            run.error_message = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            await db.flush()
            raise

