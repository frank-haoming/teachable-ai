from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TestPaperCreateRequest(BaseModel):
    class_id: int
    title: str = Field(min_length=1, max_length=200)


class TestQuestionCreateRequest(BaseModel):
    question_text: str = Field(min_length=1, max_length=2000)
    option_a: str = Field(min_length=1, max_length=1000)
    option_b: str = Field(min_length=1, max_length=1000)
    option_c: str = Field(min_length=1, max_length=1000)
    option_d: str = Field(min_length=1, max_length=1000)
    correct_answer: str = Field(min_length=1, max_length=1)
    sort_order: int = 0


class TestQuestionUpdateRequest(TestQuestionCreateRequest):
    pass


class TestQuestionResponse(ORMModel):
    id: int
    paper_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    sort_order: int


class TestPaperResponse(ORMModel):
    id: int
    class_id: int
    teacher_id: int
    title: str
    created_at: datetime
    questions: list[TestQuestionResponse] = []


class TestRunResponse(ORMModel):
    id: int
    paper_id: int
    class_id: int
    status: str
    progress_completed: int
    progress_total: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class TestResultItem(BaseModel):
    student_id: int
    student_name: str
    score: int
    total: int
    detail: dict[str, Any]
    tested_at: datetime
