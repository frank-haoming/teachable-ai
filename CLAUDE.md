# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Apprentice AI** is a "Learning by Teaching" (以教促学) English grammar learning platform. Students teach grammar rules to an AI student; the AI remembers what each student taught it, and is later tested — revealing gaps in the student's understanding.

## Commands

### Backend (Python / FastAPI)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in values
uvicorn app.main:app --reload  # dev server on :8000
```

**Tests:**
```bash
pytest backend/tests/                                           # all tests
pytest backend/tests/test_auth_and_teach.py                    # single file
pytest backend/tests/test_auth_and_teach.py::test_func_name    # single test
```

Tests use SQLite in-memory (auto-schema) — no external DB needed. Async tests run via `pytest-asyncio` (configured in `backend/tests/conftest.py`).

**Database migrations (production):**
```bash
cd backend
alembic upgrade head              # apply all pending migrations
alembic revision --autogenerate -m "description"  # generate new migration
```

In dev, `AUTO_CREATE_SCHEMA=true` in `.env` bypasses Alembic and lets SQLAlchemy create tables directly.

### Frontend (Vue 3 / Vite)
```bash
cd frontend
npm install
cp .env.example .env           # set VITE_API_BASE_URL
npm run dev                    # dev server on :5173
npm run build && npm run preview
```

### Docker (full stack)
```bash
cp backend/.env.example backend/.env   # configure first
docker compose up --build
```

Set `MOCK_AI_ENABLED=true` in `backend/.env` to run without a DeepSeek API key.

## Architecture

### Data Flow — Core "Teach" Loop
1. Student sends message → `POST /api/chat/sessions/{id}/messages`
2. `ChatService` calls `AIService.extract_knowledge()` → DeepSeek extracts grammar points
3. `KnowledgeService.merge_knowledge()` semantically folds new points into the student's JSONB knowledge base (`AIKnowledge` table)
4. `AIService.generate_response()` creates the AI student reply, grounded in `ChatSession` history + a rolling `SessionSummary`
5. Everything (message, extracted knowledge, updated base) is persisted atomically

### Backend Layer Map
```
routers/   → HTTP interface (FastAPI)
services/  → Business logic (ChatService, AIService, KnowledgeService, TestService)
models/    → SQLAlchemy ORM
schemas/   → Pydantic request/response contracts
prompts/   → LLM prompt templates (teach, extract, summary, self_test, test_answer, knowledge_edit)
utils/     → Shared helpers
```

Key files:
- `backend/app/main.py` — app init, router registration
- `backend/app/config.py` — all env vars via Pydantic Settings
- `backend/app/services/ai_service.py` — DeepSeek integration + mock mode
- `backend/app/services/knowledge_service.py` — JSONB knowledge CRUD & semantic merge
- `backend/app/services/worker.py` — background test runner (DB polling, no Redis)

### Frontend Layer Map
```
views/     → Page components (auth/, student/, teacher/)
components/→ Reusable UI (AppShell, ChatBubble, KnowledgePanel, …)
stores/    → Pinia: auth.js, chat.js
api/       → Axios modules mirroring backend routers
router/    → Vue Router with role-based guards (student / teacher)
```

### Knowledge Storage
Each student has one `AIKnowledge` row per class (JSONB column). Topics: `subject_clause`, `object_clause`, `predicative_clause`, `appositive_clause`, `general`, `other`. Merge decisions: `new | supplement | revise | ignore`. Changes are audit-logged in `KnowledgeChangeLog`.

### Session Summarisation
After `SESSION_SUMMARY_TRIGGER_TURNS` messages (default 20), `ChatService` calls `AIService.generate_summary()` and stores it in `SessionSummary`. Subsequent context windows use this summary + the last `SESSION_RECENT_MESSAGES` (default 6) messages.

### Async Test Runner
`worker.py` polls the database every `TEST_WORKER_POLL_INTERVAL_SECONDS` (default 2 s) for pending `TestRun` jobs — no Redis or Celery required. Lifecycle: `claim_next_run` → `execute_run` → update status. Session types (defined in `utils/constants.py`): `teach`, `student_test_mcq`, `student_test_open`.

## Environment Variables (important ones)
| Variable | Purpose |
|---|---|
| `MOCK_AI_ENABLED` | `true` → stub AI responses, no API key needed |
| `TEACHER_REG_CODE` | Required to register as a teacher |
| `DATABASE_URL` | PostgreSQL (prod) or `sqlite+aiosqlite:///./dev.db` |
| `AUTO_CREATE_SCHEMA` | `true` → SQLAlchemy creates tables on startup (dev only; use Alembic in prod) |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` | LLM credentials |
| `JWT_SECRET_KEY` / `JWT_EXPIRE_MINUTES` | Auth token signing (default expiry: 1440 min) |

## Critical Files
- `backend/app/prompts/` — changing prompts here directly affects AI behaviour
- `backend/app/services/knowledge_service.py` — merge logic is the core algorithm
- `frontend/src/api/index.js` — Axios base config and auth token injection
- `frontend/src/router/index.js` — route guards; update when adding new roles/pages
