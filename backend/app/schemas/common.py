from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class TimeStampedItem(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DynamicPayload(BaseModel):
    data: dict[str, Any]

