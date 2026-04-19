from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    course_topic: str | None = Field(default=None, max_length=100)
    subject_description: str | None = Field(default=None, max_length=300)
    covered_topics: list[str] = Field(default_factory=list)
    knowledge_focuses: list[str] = Field(default_factory=list)


class ClassConfigUpdateRequest(BaseModel):
    course_topic: str | None = Field(default=None, max_length=100)
    subject_description: str | None = Field(default=None, max_length=300)
    covered_topics: list[str] = Field(default_factory=list)
    knowledge_focuses: list[str] = Field(default_factory=list)


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
    course_topic: str
    subject_description: str
    covered_topics: list[str]
    covered_topic_labels: list[str]
    knowledge_focuses: list[str]
    student_count: int
    knowledge_item_count: int
    students: list[StudentSummary]
