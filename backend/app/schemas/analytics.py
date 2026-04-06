from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ClassOverviewResponse(BaseModel):
    class_id: int
    student_count: int
    topic_coverage: dict[str, int]
    average_knowledge_items: float
    latest_test_average: float | None


class StudentAnalyticsItem(BaseModel):
    student_id: int
    student_name: str
    knowledge_items: int
    latest_score: int | None
    latest_total: int | None
    corrections: int


class StudentProgressResponse(BaseModel):
    student_id: int
    class_id: int
    timeline: list[dict[str, Any]]
    tests: list[dict[str, Any]]

