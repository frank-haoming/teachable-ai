from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    subject_description: str | None = Field(default=None, max_length=300)


class ClassJoinRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=10)


class StudentSummary(ORMModel):
    id: int
    display_name: str
    username: str


class ClassResponse(ORMModel):
    id: int
    name: str
    invite_code: str
    created_at: datetime


class ClassDetailResponse(BaseModel):
    id: int
    name: str
    invite_code: str
    created_at: datetime
    teacher_name: str
    student_count: int
    knowledge_item_count: int
    students: list[StudentSummary]
