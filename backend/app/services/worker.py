from __future__ import annotations

import asyncio
import contextlib

from app.config import get_settings
from app.database import SessionLocal
from app.services.test_service import TestService


class TestRunWorker:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._settings = get_settings()
        self._service = TestService()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _loop(self) -> None:
        while self._running:
            if SessionLocal is None:
                await asyncio.sleep(self._settings.test_worker_poll_interval_seconds)
                continue
            async with SessionLocal() as db:
                run = await self._service.claim_next_run(db)
                if run is None:
                    await db.commit()
                    await asyncio.sleep(self._settings.test_worker_poll_interval_seconds)
                    continue
                run_id = run.id
                await db.commit()
            async with SessionLocal() as exec_db:
                real_run = await exec_db.get(type(run), run_id)
                if real_run is not None:
                    try:
                        await self._service.execute_run(exec_db, real_run)
                        await exec_db.commit()
                    except Exception:  # noqa: BLE001
                        await exec_db.commit()
            await asyncio.sleep(0)
