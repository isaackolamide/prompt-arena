# gemini-llm-proxy Implementation Plan

**Goal:** Build a secure, rate-limited, and token-metered backend proxy for Google Gemini API calls, enforcing session-bound token budgets and protecting secrets.
**Architecture:** Expose a POST `/challenges/session/{session_id}/prompt` endpoint. It validates session state and budget, calls the Google Generative AI Python SDK (`gemini-1.5-flash`) with strict timeouts and error translations, and atomically decrements the session's token budget on the database engine using a PL/pgSQL RPC database function.
**Tech Stack:** Python 3.10+, FastAPI, Supabase Python Client, pytest, google-generativeai, PostgreSQL.

---

## Phase 1: Database Migration & Schema Setup

### Task 1.1: Database Migration Script
- [x] Task Completed
- Scope: S
- Files:
  - `supabase/migrations/20260626000000_add_game_sessions_token_budget.sql` (create)
  - `backend/app/db/schema.sql` (modify)
- Interfaces:
  - Stored database function: `deduct_session_budget(session_id uuid, tokens_to_deduct int) -> int` (returns updated remaining budget, raises exception on insufficient budget)
- Acceptance criteria:
  - Stored function executes atomically. If budget is insufficient, it rolls back and raises an exception.
  - `public.game_sessions` has `token_budget` column of type `integer` with a check constraint `token_budget >= 0` and default of `0`.
- Verification: Run `make start` and verify migrations apply without error.
- Dependencies: None

### Task 1.2: Database Integration Tests
- [x] Task Completed
- Scope: M
- Files:
  - `backend/tests/integration/test_database_budget.py` (create)
- Interfaces:
  - Test case: `test_deduct_session_budget_success(db_client: Client) -> None`
  - Test case: `test_deduct_session_budget_insufficient(db_client: Client) -> None`
  - Test case: `test_deduct_session_budget_missing(db_client: Client) -> None`
- Acceptance criteria:
  - Integration tests verify token budget updates atomically, constraints are enforced, and RPC exceptions are correctly thrown.
- Verification: Run `pytest backend/tests/integration/test_database_budget.py`
- Dependencies: Task 1.1

### Checkpoint — Phase 1
- [x] Supabase database schema migrations apply cleanly, and all budget-related integration tests pass successfully.
- Verification: `pytest backend/tests/integration/test_database_budget.py`

---

## Phase 2: Dependency & Auth Guard Setup

### Task 2.1: Dependencies & Settings Config
- [x] Task Completed
- Scope: S
- Files:
  - `backend/requirements.txt` (modify)
  - `backend/app/core/config.py` (modify)
- Interfaces:
  - Adds `google-generativeai>=0.8.0` to dependencies.
  - Exposes `Settings.GEMINI_API_KEY: str` configuration.
- Acceptance criteria:
  - Settings load successfully. Packages install cleanly.
- Verification: Run `make build`
- Dependencies: None

### Task 2.2: Auth Guard Dependency
- [x] Task Completed
- Scope: M
- Files:
  - `backend/app/api/dependencies.py` (create)
- Interfaces:
  - Produces: `async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str` (returns the authenticated user UUID)
- Acceptance criteria:
  - Rejects missing, invalid, or expired tokens with `401 Unauthorized`.
  - Verifies token validity using Supabase authentication `client.auth.get_user(token)`.
- Verification: Run `pytest backend/tests/unit/test_auth_guard.py`
- Dependencies: Task 2.1

### Checkpoint — Phase 2
- [x] Auth guard dependency is fully covered by tests, and libraries are installed cleanly.
- Verification: `pytest backend/tests/unit/test_auth_guard.py`

---

## Phase 3: Core LLM Proxy Service & Endpoint

### Task 3.1: LLM Proxy Service
- [ ] Task Completed
- Scope: L
- Files:
  - `backend/app/services/llm_proxy.py` (create)
- Interfaces:
  - Produces: `async def execute_prompt(session_id: uuid.UUID, prompt: str, user_id: str) -> dict[str, Any]` (returns dict containing: `{"response": str, "tokens_used": int, "remaining_budget": int}`)
  - Consumes: Google Generative AI Python SDK and Supabase client methods.
- Acceptance criteria:
  - Session verification checks if session status is `'in_progress'` and belongs to the authenticated player `user_id`. Throws custom error mapped to `403 Forbidden` if validation fails.
  - Checks if session's remaining budget is > 0 (else throws error mapped to `403 Forbidden`).
  - Limits prompt length to 10,000 characters (else throws error mapped to `400 Bad Request`).
  - Initiates Gemini client `gemini-1.5-flash` using `GEMINI_API_KEY` and challenge system prompt. Injects simple guardrails preventing code output dumps.
  - Gracefully handles dummy or unconfigured `GEMINI_API_KEY` values in development/testing (e.g. if the key is empty, missing, or set to a placeholder, return a deterministic mock response without making upstream network calls).
  - Restricts upstream call with a 10-second timeout.
  - Atomically decrements budget using `deduct_session_budget` RPC on success.
  - Maps upstream errors (429 status for rate limits, 502 Bad Gateway for other failures). Ensures no tokens are deducted on model call failure.
- Verification: Run `pytest backend/tests/unit/test_llm_proxy_service.py`
- Dependencies: Task 1.1, Task 2.1

### Task 3.2: FastAPI Router / Endpoint
- [ ] Task Completed
- Scope: M
- Files:
  - `backend/app/api/challenges.py` (create)
  - `backend/app/schemas/challenges.py` (create)
  - `backend/app/schemas/__init__.py` (modify)
  - `backend/app/main.py` (modify)
- Interfaces:
  - Produces route: `POST /challenges/session/{session_id}/prompt`
  - Produces schema: `class PromptRequest(BaseModel)` with `prompt: str`
  - Produces schema: `class PromptResponse(BaseModel)` with `response: str`, `tokens_used: int`, and `remaining_budget: int`
  - Consumes auth: `get_current_user`
  - Consumes service: `execute_prompt(session_id: uuid.UUID, prompt: str, user_id: str) -> dict[str, Any]`
- Acceptance criteria:
  - Endpoint requires Bearer token, validates input payload and route parameters, routes validation exceptions, and returns responses.
- Verification: Run `pytest backend/tests/integration/test_challenges_api.py`
- Dependencies: Task 2.2, Task 3.1

### Checkpoint — Phase 3
- [ ] Full proxy flow is verified and both unit and integration tests pass successfully.
- Verification: Run `make test`

---

## Plan Code Review
- [ ] Feature plan code review passed
