from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ChatMessage, ChatSession, SessionSummary
from app.services.ai_service import AIService
from app.services.knowledge_service import KnowledgeService
from app.utils.constants import SESSION_TYPE_STUDENT_TEST_FREE, SESSION_TYPE_STUDENT_TEST_MCQ, SESSION_TYPE_TEACH


class ChatService:
    def __init__(self, ai_service: AIService | None = None, knowledge_service: KnowledgeService | None = None) -> None:
        self.ai_service = ai_service or AIService.build()
        self.knowledge_service = knowledge_service or KnowledgeService(ai_service=self.ai_service)
        self.settings = get_settings()

    async def create_session(
        self,
        db: AsyncSession,
        student_id: int,
        class_id: int,
        session_type: str,
        title: str | None = None,
        ai_name: str | None = None,
    ) -> ChatSession:
        session = ChatSession(
            student_id=student_id,
            class_id=class_id,
            session_type=session_type,
            title=title,
            ai_name=ai_name,
        )
        db.add(session)
        await db.flush()
        return session

    async def list_sessions(
        self,
        db: AsyncSession,
        student_id: int,
        class_id: int | None = None,
        session_type: str | None = None,
    ) -> list[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.student_id == student_id)
        if class_id is not None:
            stmt = stmt.where(ChatSession.class_id == class_id)
        if session_type is not None:
            stmt = stmt.where(ChatSession.session_type == session_type)
        stmt = stmt.order_by(ChatSession.updated_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_messages(self, db: AsyncSession, session_id: int) -> list[ChatMessage]:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def send_message(
        self,
        db: AsyncSession,
        session: ChatSession,
        user_id: int,
        content: str,
    ) -> tuple[ChatMessage, ChatMessage, bool, dict | None, int | None]:
        self.settings = get_settings()
        user_message = ChatMessage(session_id=session.id, role="user", content=content, meta={"mode": session.session_type})
        db.add(user_message)
        await db.flush()

        knowledge_changed = False
        extracted = None
        knowledge_version = None
        knowledge = await self.knowledge_service.get_or_create_knowledge(db, session.student_id, session.class_id)

        if session.session_type == SESSION_TYPE_TEACH:
            # Auto-title the session from first user message
            if session.title in (None, "Teach Session", ""):
                count_res = await db.execute(
                    select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session.id)
                )
                if (count_res.scalar() or 0) <= 1:
                    session.title = content[:24] + ("…" if len(content) > 24 else "")
            extracted = await self.ai_service.extract_knowledge(content)
            user_message.knowledge_extracted = extracted if extracted.get("has_knowledge") else None
            if extracted.get("has_knowledge"):
                knowledge_changed = await self.knowledge_service.apply_extractions(
                    db,
                    knowledge,
                    extracted["items"],
                    actor_user_id=user_id,
                    source="dialogue",
                )
            flat = self.knowledge_service.flatten_knowledge(knowledge.knowledge_data)
            summary = await self._latest_summary(db, session.id)
            recent_messages = await self._recent_messages(db, session.id)
            assistant_content = await self.ai_service.generate_teach_reply(
                flat, summary, recent_messages, ai_name=session.ai_name
            )
            knowledge_version = knowledge.version
        elif session.session_type == SESSION_TYPE_STUDENT_TEST_FREE:
            flat = self.knowledge_service.flatten_knowledge(knowledge.knowledge_data)
            recent_messages = await self._recent_messages(db, session.id)
            answer = await self.ai_service.answer_question(
                flat,
                content,
                conversational=True,
                history=recent_messages,
            )
            assistant_content = answer["content"]
            knowledge_version = knowledge.version
        else:
            raise ValueError("Use answer_student_mcq for MCQ sessions.")

        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_content,
            meta={"mode": session.session_type},
        )
        db.add(assistant_message)
        session.updated_at = datetime.now(timezone.utc)
        await db.flush()

        if session.session_type == SESSION_TYPE_TEACH:
            await self._maybe_refresh_summary(db, session.id)

        return user_message, assistant_message, knowledge_changed, extracted, knowledge_version

    async def answer_student_mcq(
        self,
        db: AsyncSession,
        session: ChatSession,
        user_id: int,
        question_text: str,
        options: dict[str, str],
    ) -> tuple[ChatMessage, ChatMessage]:
        if session.session_type != SESSION_TYPE_STUDENT_TEST_MCQ:
            raise ValueError("This session does not accept MCQ answers.")
        knowledge = await self.knowledge_service.get_or_create_knowledge(db, session.student_id, session.class_id)
        flat = self.knowledge_service.flatten_knowledge(knowledge.knowledge_data)
        answer = await self.ai_service.answer_question(flat, question_text, options=options)
        user_payload = {
            "question_text": question_text,
            "options": options,
            "mode": session.session_type,
        }
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=question_text,
            meta=user_payload,
        )
        db.add(user_message)
        await db.flush()
        assistant_content = f'我的选择是 {answer["answer"]}。{answer["reasoning"]}'
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_content,
            meta={
                "mode": session.session_type,
                "answer": answer["answer"],
                "reasoning": answer["reasoning"],
            },
        )
        db.add(assistant_message)
        session.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return user_message, assistant_message

    async def _recent_messages(self, db: AsyncSession, session_id: int) -> list[dict[str, str]]:
        limit = self.settings.session_recent_messages * 2
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": message.role, "content": message.content} for message in messages]

    async def _latest_summary(self, db: AsyncSession, session_id: int) -> str | None:
        result = await db.execute(
            select(SessionSummary)
            .where(SessionSummary.session_id == session_id)
            .order_by(SessionSummary.generated_at.desc())
            .limit(1)
        )
        summary = result.scalar_one_or_none()
        return summary.summary_content if summary else None

    async def _maybe_refresh_summary(self, db: AsyncSession, session_id: int) -> None:
        total_result = await db.execute(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        total_messages = total_result.scalar() or 0
        trigger = self.settings.session_summary_trigger_turns * 2  # both sides of conversation
        if total_messages < trigger:
            return
        # Only generate at multiples of trigger (e.g. 40th, 80th, 120th message)
        summary_count_result = await db.execute(
            select(func.count()).select_from(SessionSummary).where(SessionSummary.session_id == session_id)
        )
        existing_count = summary_count_result.scalar() or 0
        expected_count = total_messages // trigger
        if existing_count >= expected_count:
            return
        # Build summary from all messages so far
        msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(msg_result.scalars().all())
        payload = [{"role": m.role, "content": m.content} for m in messages]
        summary = await self.ai_service.summarize_messages(payload)
        db.add(SessionSummary(session_id=session_id, summary_content=summary))
        await db.flush()
