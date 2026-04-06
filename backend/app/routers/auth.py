from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import ClassRoom, ClassStudent, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UpdateProfileRequest, UserResponse
from app.services.knowledge_service import KnowledgeService
from app.utils.constants import ROLE_STUDENT, ROLE_TEACHER, ROLES
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    if payload.role not in ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role.")
    if payload.role == ROLE_TEACHER and payload.teacher_reg_code != settings.teacher_registration_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid teacher registration code.")

    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
    )
    db.add(user)
    await db.flush()

    if payload.role == ROLE_STUDENT and payload.invite_code:
        classroom_result = await db.execute(select(ClassRoom).where(ClassRoom.invite_code == payload.invite_code))
        classroom = classroom_result.scalar_one_or_none()
        if classroom is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite code not found.")
        db.add(
            ClassStudent(
                class_id=classroom.id,
                student_id=user.id,
                joined_at=datetime.now(timezone.utc),
            )
        )
        knowledge_service = KnowledgeService()
        await knowledge_service.get_or_create_knowledge(db, user.id, classroom.id, classroom.knowledge_template)

    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    return TokenResponse(access_token=create_access_token(user.id, user.role), user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    if payload.new_password:
        if not payload.current_password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="当前密码不能为空。")
        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前密码不正确。")
        current_user.password_hash = hash_password(payload.new_password)
    if payload.display_name:
        current_user.display_name = payload.display_name
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

