from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user, require_student, require_teacher
from app.models import AIKnowledge, ClassRoom, ClassStudent, User
from app.schemas.class_ import ClassCreateRequest, ClassDetailResponse, ClassJoinRequest, ClassResponse, StudentSummary
from app.services.knowledge_service import KnowledgeService
from app.utils.constants import ROLE_STUDENT
from app.utils.invite import generate_invite_code
from app.utils.qrcode import generate_qr_png
from app.utils.constants import build_default_knowledge_template

router = APIRouter(prefix="/classes", tags=["classes"])


async def _get_classroom_or_404(db: AsyncSession, class_id: int) -> ClassRoom:
    result = await db.execute(select(ClassRoom).where(ClassRoom.id == class_id))
    classroom = result.scalar_one_or_none()
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    return classroom


async def _ensure_student_membership(db: AsyncSession, class_id: int, student_id: int) -> None:
    membership_result = await db.execute(
        select(ClassStudent).where(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
    )
    if membership_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this class.")


@router.post("", response_model=ClassResponse)
async def create_class(
    payload: ClassCreateRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> ClassResponse:
    invite_code = generate_invite_code()
    while True:
        existing = await db.execute(select(ClassRoom).where(ClassRoom.invite_code == invite_code))
        if existing.scalar_one_or_none() is None:
            break
        invite_code = generate_invite_code()

    classroom = ClassRoom(
        name=payload.name,
        teacher_id=teacher.id,
        invite_code=invite_code,
        knowledge_template=build_default_knowledge_template(payload.subject_description),
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return ClassResponse.model_validate(classroom)


@router.get("")
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if current_user.role == ROLE_STUDENT:
        stmt = (
            select(ClassRoom, AIKnowledge)
            .join(ClassStudent, ClassStudent.class_id == ClassRoom.id)
            .outerjoin(
                AIKnowledge,
                (AIKnowledge.class_id == ClassRoom.id) & (AIKnowledge.student_id == current_user.id),
            )
            .where(ClassStudent.student_id == current_user.id)
            .order_by(ClassRoom.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        knowledge_service = KnowledgeService()
        return [
            {
                "id": classroom.id,
                "name": classroom.name,
                "invite_code": classroom.invite_code,
                "created_at": classroom.created_at,
                "knowledge_item_count": knowledge_service.count_items(knowledge.knowledge_data if knowledge else {}),
            }
            for classroom, knowledge in rows
        ]

    stmt = (
        select(
            ClassRoom,
            func.count(ClassStudent.id).label("student_count"),
        )
        .outerjoin(ClassStudent, ClassStudent.class_id == ClassRoom.id)
        .where(ClassRoom.teacher_id == current_user.id)
        .group_by(ClassRoom.id)
        .order_by(ClassRoom.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        {
            "id": classroom.id,
            "name": classroom.name,
            "invite_code": classroom.invite_code,
            "created_at": classroom.created_at,
            "student_count": student_count,
            "subject_description": (classroom.knowledge_template or {}).get("meta", {}).get("subject_description") or "",
        }
        for classroom, student_count in result.all()
    ]


@router.get("/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassDetailResponse:
    classroom = await _get_classroom_or_404(db, class_id)
    if current_user.role == ROLE_STUDENT:
        await _ensure_student_membership(db, class_id, current_user.id)
    elif classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this class.")

    teacher = await db.get(User, classroom.teacher_id)
    student_rows = await db.execute(
        select(User)
        .join(ClassStudent, ClassStudent.student_id == User.id)
        .where(ClassStudent.class_id == class_id)
        .order_by(User.display_name.asc())
    )
    students = list(student_rows.scalars().all())
    knowledge_rows = await db.execute(select(AIKnowledge).where(AIKnowledge.class_id == class_id))
    knowledge_records = list(knowledge_rows.scalars().all())
    knowledge_service = KnowledgeService()
    return ClassDetailResponse(
        id=classroom.id,
        name=classroom.name,
        invite_code=classroom.invite_code,
        created_at=classroom.created_at,
        teacher_name=teacher.display_name if teacher else "",
        student_count=len(students),
        knowledge_item_count=sum(knowledge_service.count_items(record.knowledge_data) for record in knowledge_records),
        students=[StudentSummary.model_validate(student) for student in students],
    )


@router.post("/join")
async def join_class(
    payload: ClassJoinRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
) -> dict:
    classroom_result = await db.execute(select(ClassRoom).where(ClassRoom.invite_code == payload.invite_code))
    classroom = classroom_result.scalar_one_or_none()
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite code not found.")
    membership_result = await db.execute(
        select(ClassStudent).where(ClassStudent.class_id == classroom.id, ClassStudent.student_id == student.id)
    )
    if membership_result.scalar_one_or_none() is None:
        db.add(
            ClassStudent(
                class_id=classroom.id,
                student_id=student.id,
                joined_at=datetime.now(timezone.utc),
            )
        )
    knowledge_service = KnowledgeService()
    await knowledge_service.get_or_create_knowledge(db, student.id, classroom.id, classroom.knowledge_template)
    await db.commit()
    return {"message": "Joined class successfully.", "class_id": classroom.id}


@router.get("/{class_id}/invite-qrcode")
async def get_invite_qrcode(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
) -> Response:
    classroom = await _get_classroom_or_404(db, class_id)
    if classroom.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this class.")
    invite_url = f'{get_settings().frontend_url.rstrip("/")}/register?code={classroom.invite_code}'
    return Response(content=generate_qr_png(invite_url), media_type="image/png")
