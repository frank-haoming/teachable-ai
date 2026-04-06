from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SessionCreateRequest(BaseModel):
    class_id: int
    session_type: str
    title: str | None = Field(default=None, max_length=200)


class SessionResponse(ORMModel):
    id: int
    class_id: int
    session_type: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageItem(ORMModel):
    id: int
    session_id: int
    role: str
    content: str
    knowledge_extracted: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime


class SendMessageRequest(BaseModel):
    session_id: int
    content: str = Field(min_length=1, max_length=4000)


class SendMessageResponse(BaseModel):
    user_message: MessageItem
    assistant_message: MessageItem
    knowledge_changed: bool
    extracted: dict[str, Any] | None = None
    knowledge_version: int | None = None


class StudentMCQRequest(BaseModel):
    session_id: int
    question_text: str = Field(min_length=1, max_length=2000)
    option_a: str = Field(min_length=1, max_length=1000)
    option_b: str = Field(min_length=1, max_length=1000)
    option_c: str = Field(min_length=1, max_length=1000)
    option_d: str = Field(min_length=1, max_length=1000)
