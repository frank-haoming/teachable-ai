from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    role: str
    invite_code: str | None = None
    teacher_reg_code: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(ORMModel):
    id: int
    username: str
    display_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=6, max_length=128)

