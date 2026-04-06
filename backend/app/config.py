from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_csv(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Apprentice AI API"))
    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./apprentice_ai.db",
        )
    )
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "change-me-in-production"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expire_minutes: int = field(default_factory=lambda: _env_int("JWT_EXPIRE_MINUTES", 60 * 24))
    teacher_registration_code: str = field(
        default_factory=lambda: os.getenv(
            "TEACHER_REG_CODE",
            "APPRENTICE-TEACHER",
        )
    )
    frontend_url: str = field(default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173"))
    cors_origins: list[str] = field(
        default_factory=lambda: _env_csv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
    )
    deepseek_base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    mock_ai_enabled: bool = field(default_factory=lambda: _env_bool("MOCK_AI_ENABLED", True))
    session_summary_trigger_turns: int = field(default_factory=lambda: _env_int("SESSION_SUMMARY_TRIGGER_TURNS", 20))
    session_recent_messages: int = field(default_factory=lambda: _env_int("SESSION_RECENT_MESSAGES", 6))
    test_worker_poll_interval_seconds: int = field(
        default_factory=lambda: _env_int("TEST_WORKER_POLL_INTERVAL_SECONDS", 2)
    )
    auto_create_schema: bool = field(default_factory=lambda: _env_bool("AUTO_CREATE_SCHEMA", True))


def validate_settings(settings: Settings) -> None:
    if settings.app_env.lower() != "production":
        return
    if settings.jwt_secret in {"change-me", "change-me-in-production"}:
        raise RuntimeError("JWT_SECRET uses the default insecure value in production.")
    if settings.teacher_registration_code == "APPRENTICE-TEACHER":
        raise RuntimeError("TEACHER_REG_CODE uses the default value in production.")
    if settings.debug:
        raise RuntimeError("DEBUG must be false in production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
