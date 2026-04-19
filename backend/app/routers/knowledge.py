from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_student
from app.models import AIKnowledge, ClassStudent, KnowledgeChangeLog, User
from app.schemas.knowledge import (
    DirectKnowledgeUpdateRequest,
    FlatKnowledgeItem,
    KnowledgeChangeLogItem,
    KnowledgeCorrectionRequest,
    KnowledgeCorrectionResponse,
    KnowledgeResponse,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
knowledge_service = KnowledgeService()


async def _get_student_knowledge(db: AsyncSession, class_id: int, student_id: int) -> AIKnowledge:
    membership = await db.execute(
        select(ClassStudent).where(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this class.")
    return await knowledge_service.get_or_create_knowledge(db, student_id, class_id)


@router.get("/{class_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> KnowledgeResponse:
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    return KnowledgeResponse(
        knowledge_data=knowledge.knowledge_data,
        version=knowledge.version,
        updated_at=knowledge.updated_at,
    )


@router.get("/{class_id}/flat", response_model=list[FlatKnowledgeItem])
async def get_flat_knowledge(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> list[FlatKnowledgeItem]:
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    return [FlatKnowledgeItem.model_validate(item) for item in knowledge_service.flatten_knowledge(knowledge.knowledge_data)]


@router.post("/{class_id}/correct", response_model=KnowledgeCorrectionResponse)
async def correct_knowledge(
    class_id: int,
    payload: KnowledgeCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> KnowledgeCorrectionResponse:
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    result = await knowledge_service.apply_dialogue_correction(db, knowledge, payload.message, student.id)
    await db.commit()
    return KnowledgeCorrectionResponse(**result)


@router.put("/items/{item_id}", response_model=KnowledgeCorrectionResponse)
async def update_knowledge_item(
    item_id: str,
    payload: DirectKnowledgeUpdateRequest,
    class_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> KnowledgeCorrectionResponse:
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    try:
        await knowledge_service.update_item(db, knowledge, item_id, payload.model_dump(), student.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await db.commit()
    return KnowledgeCorrectionResponse(action="update", target_item_id=item_id, version=knowledge.version)


@router.delete("/items/{item_id}", response_model=KnowledgeCorrectionResponse)
async def delete_knowledge_item(
    item_id: str,
    class_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> KnowledgeCorrectionResponse:
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    try:
        await knowledge_service.delete_item(db, knowledge, item_id, student.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await db.commit()
    return KnowledgeCorrectionResponse(action="delete", target_item_id=item_id, version=knowledge.version)


@router.get("/{class_id}/changelog", response_model=list[KnowledgeChangeLogItem])
async def get_knowledge_changelog(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> list[KnowledgeChangeLogItem]:
    """Return the 30 most recent knowledge change log entries for this student in this class."""
    knowledge = await _get_student_knowledge(db, class_id, student.id)
    result = await db.execute(
        select(KnowledgeChangeLog)
        .where(KnowledgeChangeLog.knowledge_id == knowledge.id)
        .order_by(KnowledgeChangeLog.created_at.desc())
        .limit(30)
    )
    return [KnowledgeChangeLogItem.model_validate(log) for log in result.scalars().all()]

