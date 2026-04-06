from __future__ import annotations

from copy import deepcopy

ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLES = {ROLE_TEACHER, ROLE_STUDENT}

SESSION_TYPE_TEACH = "teach"
SESSION_TYPE_STUDENT_TEST_FREE = "student_test_free"
SESSION_TYPE_STUDENT_TEST_MCQ = "student_test_mcq"
SESSION_TYPES = {
    SESSION_TYPE_TEACH,
    SESSION_TYPE_STUDENT_TEST_FREE,
    SESSION_TYPE_STUDENT_TEST_MCQ,
}

RUN_STATUS_QUEUED = "queued"
RUN_STATUS_IN_PROGRESS = "in_progress"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"

TOPIC_META = {
    "subject_clause": "主语从句",
    "object_clause": "宾语从句",
    "predicative_clause": "表语从句",
    "appositive_clause": "同位语从句",
    "general": "通用知识",
    "other": "偏好与其他",
}


def build_default_knowledge_template(subject_description: str | None = None) -> dict:
    template: dict = {
        "topics": {
            key: {
                "name": name,
                "knowledge": [],
                "examples": [],
            }
            for key, name in TOPIC_META.items()
        },
        "version": 1,
        "updated_at": None,
    }
    if subject_description:
        template["meta"] = {"subject_description": subject_description}
    return template


def clone_knowledge_template(template: dict | None = None) -> dict:
    return deepcopy(template or build_default_knowledge_template())

