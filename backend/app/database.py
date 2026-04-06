from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base

engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def configure_database(database_url: str | None = None) -> None:
    global engine, SessionLocal
    settings = get_settings()
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_async_engine(url, echo=settings.debug, future=True, connect_args=connect_args)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


configure_database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise RuntimeError("Database is not configured.")
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    if engine is None:
        raise RuntimeError("Database engine is not configured.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    if engine is not None:
        await engine.dispose()

