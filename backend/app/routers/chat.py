from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_student
from app.models import ChatMessage, ChatSession, ClassStudent, User
from app.schemas.chat import (
    MessageItem,
    SendMessageRequest,
    SendMessageResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionUpdateRequest,
    StudentMCQRequest,
)
from app.services.chat_service import ChatService
from app.utils.constants import SESSION_TYPES

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


async def _student_has_class_access(db: AsyncSession, class_id: int, student_id: int) -> None:
    result = await db.execute(
        select(ClassStudent).where(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this class.")


async def _get_owned_session(db: AsyncSession, session_id: int, student_id: int) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.student_id == student_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> SessionResponse:
    if payload.session_type not in SESSION_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session type.")
    await _student_has_class_access(db, payload.class_id, student.id)
    session = await chat_service.create_session(
        db, student.id, payload.class_id, payload.session_type, payload.title, payload.ai_name
    )
    await db.commit()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    class_id: int | None = None,
    session_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> list[SessionResponse]:
    sessions = await chat_service.list_sessions(db, student.id, class_id=class_id, session_type=session_type)
    return [SessionResponse.model_validate(session) for session in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageItem])
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> list[MessageItem]:
    session = await _get_owned_session(db, session_id, student.id)
    messages = await chat_service.get_messages(db, session.id)
    return [MessageItem.model_validate(message) for message in messages]


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> SessionResponse:
    session = await _get_owned_session(db, session_id, student.id)
    if payload.ai_name is not None:
        session.ai_name = payload.ai_name
    await db.commit()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/extract")
async def manual_extract(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> dict:
    session = await _get_owned_session(db, session_id, student.id)
    if session.session_type != "teach":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only teach sessions support extraction.")
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(40)
    )
    recent = list(reversed(result.scalars().all()))
    combined_text = "\n".join(f"[{m.role}] {m.content}" for m in recent)
    knowledge = await chat_service.knowledge_service.get_or_create_knowledge(db, session.student_id, session.class_id)
    extracted = await chat_service.ai_service.extract_knowledge(
        combined_text,
        learning_scope=knowledge.knowledge_data.get("meta") if knowledge.knowledge_data else None,
    )
    changed = False
    if extracted.get("has_knowledge"):
        changed = await chat_service.knowledge_service.apply_extractions(
            db, knowledge, extracted["items"], actor_user_id=student.id, source="manual_extract"
        )
    await db.commit()
    return {"changed": changed, "knowledge_version": knowledge.version}


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> SendMessageResponse:
    session = await _get_owned_session(db, payload.session_id, student.id)
    if session.session_type == "student_test_mcq":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Use the MCQ endpoint for this session.")
    user_message, assistant_message, knowledge_changed, extracted, knowledge_version = await chat_service.send_message(
        db,
        session,
        user_id=student.id,
        content=payload.content,
        focus=payload.focus,
    )
    await db.commit()
    return SendMessageResponse(
        user_message=MessageItem.model_validate(user_message),
        assistant_message=MessageItem.model_validate(assistant_message),
        knowledge_changed=knowledge_changed,
        extracted=extracted,
        knowledge_version=knowledge_version,
    )


@router.post("/classes/{class_id}/rename-ai")
async def rename_class_ai(
    class_id: int,
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> dict:
    """Bulk-update ai_name for all teach sessions belonging to this student in this class."""
    await db.execute(
        update(ChatSession)
        .where(
            ChatSession.student_id == student.id,
            ChatSession.class_id == class_id,
            ChatSession.session_type == "teach",
        )
        .values(ai_name=payload.ai_name)
    )
    await db.commit()
    return {"updated": True}


@router.post("/student-test/mcq", response_model=SendMessageResponse)
async def answer_student_mcq(
    payload: StudentMCQRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> SendMessageResponse:
    session = await _get_owned_session(db, payload.session_id, student.id)
    user_message, assistant_message = await chat_service.answer_student_mcq(
        db,
        session,
        student.id,
        question_text=payload.question_text,
        options={
            "A": payload.option_a,
            "B": payload.option_b,
            "C": payload.option_c,
            "D": payload.option_d,
        },
    )
    await db.commit()
    return SendMessageResponse(
        user_message=MessageItem.model_validate(user_message),
        assistant_message=MessageItem.model_validate(assistant_message),
        knowledge_changed=False,
        extracted=None,
        knowledge_version=None,
    )
