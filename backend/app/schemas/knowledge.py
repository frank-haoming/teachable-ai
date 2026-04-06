from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FlatKnowledgeItem(BaseModel):
    id: str
    topic: str
    topic_name: str
    item_type: str
    content: str | None = None
    sentence: str | None = None
    explanation: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class KnowledgeResponse(BaseModel):
    knowledge_data: dict[str, Any]
    version: int
    updated_at: datetime


class KnowledgeCorrectionRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class DirectKnowledgeUpdateRequest(BaseModel):
    content: str | None = Field(default=None, max_length=4000)
    sentence: str | None = Field(default=None, max_length=4000)
    explanation: str | None = Field(default=None, max_length=4000)


class KnowledgeCorrectionResponse(BaseModel):
    action: str
    target_item_id: str | None = None
    version: int


class KnowledgeChangeLogItem(ORMModel):
    id: int
    knowledge_id: int
    target_item_id: str
    item_type: str
    action: str
    source: str
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    actor_user_id: int
    created_at: datetime
