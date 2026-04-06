from __future__ import annotations

import os
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture()
async def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["MOCK_AI_ENABLED"] = "true"
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
    os.environ["TEACHER_REG_CODE"] = "APPRENTICE-TEACHER"

    from app.config import get_settings
    from app.database import configure_database, init_db
    from app.main import create_app

    get_settings.cache_clear()
    configure_database(os.environ["DATABASE_URL"])
    await init_db()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
