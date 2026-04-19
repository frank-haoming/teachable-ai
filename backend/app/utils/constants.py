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

DEFAULT_COURSE_TOPIC = "英语名词从句"
DEFAULT_COVERED_TOPICS = [
    "主语从句",
    "宾语从句",
    "表语从句",
    "同位语从句",
]
DEFAULT_KNOWLEDGE_FOCUSES = [
    "通用",
    "定义",
    "基本结构",
    "常见引导词",
    "语法功能",
    "例子",
]


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def normalize_topic_label(value: str | None) -> str:
    """Map an English TOPIC_META key to its Chinese display label. Non-key strings pass through unchanged."""
    stripped = (value or "").strip()
    return TOPIC_META.get(stripped, stripped) if stripped else ""


def normalize_covered_topics(covered_topics: list[str] | None = None) -> list[str]:
    """Preserve raw input (dedupe + trim only). No TOPIC_META mapping. Returns [] if nothing given."""
    return _dedupe_keep_order(list(covered_topics or []))


def covered_topics_to_labels(covered_topics: list[str]) -> list[str]:
    """Convert raw covered_topics to Chinese display labels via TOPIC_META for rendering/bucketing.
    Strings not in TOPIC_META (e.g. custom Chinese topics) pass through unchanged."""
    return [lbl for raw in covered_topics if (lbl := normalize_topic_label(raw))]


def normalize_knowledge_focuses(knowledge_focuses: list[str] | None = None) -> list[str]:
    focuses = _dedupe_keep_order(list(knowledge_focuses or []))
    if "通用" not in focuses:
        focuses.insert(0, "通用")
    return focuses or DEFAULT_KNOWLEDGE_FOCUSES.copy()


def build_scope_summary(covered_topics: list[str] | None = None) -> str:
    raw = normalize_covered_topics(covered_topics)
    labels = covered_topics_to_labels(raw) or list(raw) or DEFAULT_COVERED_TOPICS
    return "、".join(labels)


def build_topic_buckets(raw_topics: list[str] | None = None) -> dict:
    """Create empty topic buckets keyed by Chinese display labels."""
    raw = normalize_covered_topics(raw_topics)
    labels = covered_topics_to_labels(raw)
    if not labels:
        labels = DEFAULT_COVERED_TOPICS.copy()
    return {
        label: {
            "name": label,
            "knowledge": [],
            "examples": [],
        }
        for label in labels
    }


def infer_topic_labels(template: dict | None = None) -> list[str]:
    """Infer raw topic labels from existing topic bucket keys (already display labels in stored data)."""
    topics = (template or {}).get("topics") or {}
    inferred = []
    for topic, payload in topics.items():
        label = (payload.get("name") or topic).strip()
        if label:
            inferred.append(label)
    return _dedupe_keep_order(inferred)


def get_template_meta(template: dict | None = None) -> dict:
    meta = (template or {}).get("meta") or {}
    course_topic = (meta.get("course_topic") or DEFAULT_COURSE_TOPIC).strip()

    # Preserve raw covered_topics; fall back to inferred (display labels from bucket keys) or defaults
    raw_src = meta.get("covered_topics") or meta.get("covered_topic_labels") or infer_topic_labels(template)
    raw_topics = normalize_covered_topics(raw_src) or DEFAULT_COVERED_TOPICS.copy()
    # Map to display labels; for custom Chinese topics not in TOPIC_META, pass through as-is
    display_labels = covered_topics_to_labels(raw_topics) or list(raw_topics)

    knowledge_focuses = normalize_knowledge_focuses(meta.get("knowledge_focuses"))
    subject_description = (meta.get("subject_description") or "").strip()
    if not subject_description:
        scope_str = "\u3001".join(display_labels)
        subject_description = "\u672c\u73ed\u56f4\u7ed5\u201c" + course_topic + "\u201d\u5c55\u5f00\uff0c\u5f53\u524d\u91cd\u70b9\u8986\u76d6\uff1a" + scope_str + "\u3002"
    return {
        "course_topic": course_topic,
        "subject_description": subject_description,
        "covered_topics": raw_topics,
        "covered_topic_labels": display_labels,
        "knowledge_focuses": knowledge_focuses,
    }


def build_default_knowledge_template(
    subject_description: str | None = None,
    course_topic: str | None = None,
    covered_topics: list[str] | None = None,
    knowledge_focuses: list[str] | None = None,
) -> dict:
    course_topic = (course_topic or DEFAULT_COURSE_TOPIC).strip() or DEFAULT_COURSE_TOPIC
    raw_topics = normalize_covered_topics(covered_topics) or DEFAULT_COVERED_TOPICS.copy()
    display_labels = covered_topics_to_labels(raw_topics) or list(raw_topics)
    normalized_focuses = normalize_knowledge_focuses(knowledge_focuses)
    if not (subject_description or "").strip():
        scope_str = "\u3001".join(display_labels)
        subject_description = "\u672c\u73ed\u56f4\u7ed5\u201c" + course_topic + "\u201d\u5c55\u5f00\uff0c\u5f53\u524d\u91cd\u70b9\u8986\u76d6\uff1a" + scope_str + "\u3002"
    else:
        subject_description = (subject_description or "").strip()
    template: dict = {
        "topics": build_topic_buckets(raw_topics),
        "version": 1,
        "updated_at": None,
        "meta": {
            "course_topic": course_topic,
            "subject_description": subject_description,
            "covered_topics": raw_topics,
            "covered_topic_labels": display_labels,
            "knowledge_focuses": normalized_focuses,
        },
    }
    return template


def clone_knowledge_template(template: dict | None = None) -> dict:
    return deepcopy(template or build_default_knowledge_template())
