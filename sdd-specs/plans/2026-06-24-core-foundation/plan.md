# Core Foundation Implementation Plan

**Goal:** Establish the monorepo root structure, Supabase database schema, FastAPI backend boilerplate with Magic Link auth, local Docker executor, and pytest/vitest testing setups.
**Architecture:** Use a monorepo setup with FastAPI (Python) for API routes, Supabase client wrapper, and Docker SDK interaction. Code is executed in a containerized environment (Docker executor) mimicking the final AWS Lambda environment with time boundaries and network restrictions.
**Tech Stack:** FastAPI, Supabase Python Client, Docker SDK, Pytest, Vitest, React, TypeScript.

---

## Phase 1: Project Skeleton & Test Pipelines

### [x] Task 1.1: Monorepo Root Skeleton & Makefile
- Scope: S
- Files: `Makefile` (create), `.gitignore` (modify), `.agents/AGENTS.md` (create)
- Interfaces: produces `Makefile` CLI targets (build, test, lint, dev)
- Acceptance criteria:
  - Directory structure `backend/`, `frontend/`, and `sandbox-lambda/` is present.
  - Root `Makefile` executes targets successfully.
  - `.agents/AGENTS.md` contains the developer agent guide, commands, and styling guidelines.
- Verification: `make build` and `ls -la` inside root
- Dependencies: none

### [ ] Task 1.2: Test Frameworks & CI Config (pytest & vitest)
- Scope: S
- Files: `backend/requirements.txt` (create), `backend/tests/test_dummy.py` (create), `frontend/package.json` (create), `frontend/vite.config.ts` (create), `frontend/src/tests/dummy.test.ts` (create)
- Interfaces: produces backend pytest suite, produces frontend vitest suite
- Acceptance criteria:
  - Running `make test` runs both backend and frontend test suites and they pass.
- Verification: `make test` from root
- Dependencies: Task 1.1

### Checkpoint — Phase 1
- [ ] Root Makefile, monorepo paths, and both test runners are fully functional.
- Verification: `make test` and `make lint` execute successfully without errors.

---

## Phase 2: Database Schema & FastAPI Boilerplate

### [ ] Task 2.1: Supabase DB Schema Setup
- Scope: S
- Files: `backend/app/db/schema.sql` (create)
- Interfaces: produces SQL migration script for Supabase tables
- Acceptance criteria:
  - Schema defines tables: `profiles` (tracking user profile & daily game count), `challenges`, `game_sessions`, and `scorecards`.
- Verification: Validate SQL schema against a local PostgreSQL instance.
- Dependencies: Task 1.2

### [ ] Task 2.2: FastAPI Boilerplate, DB Client & Magic Link Auth
- Scope: M
- Files: `backend/app/main.py` (create), `backend/app/core/config.py` (create), `backend/app/db/supabase.py` (create), `backend/app/api/auth.py` (create), `backend/tests/test_auth.py` (create)
- Interfaces:
  - produces `get_supabase_client() -> supabase.client.Client`
  - produces `send_magic_link(email: str) -> dict[str, str]` (returns `{"status": str}`)
  - produces `verify_otp(email: str, token: str) -> dict[str, str]` (returns `{"access_token": str}`)
- Acceptance criteria:
  - FastAPI app exposes `/api/auth/magic-link` and `/api/auth/verify` endpoints.
  - Integration/unit tests mock-verify Magic Link sending and OTP token return.
- Verification: `pytest backend/tests/test_auth.py`
- Dependencies: Task 2.1

### Checkpoint — Phase 2
- [ ] Database schema is defined, FastAPI application boots, and auth endpoints pass tests with a mocked Supabase client.
- Verification: `pytest backend/tests/test_auth.py` passes successfully.

---

## Phase 3: Local Code Execution Sandbox

### [ ] Task 3.1: Sandbox Container Image (Docker)
- Scope: S
- Files: `sandbox-lambda/Dockerfile` (create), `sandbox-lambda/runner.py` (create)
- Interfaces: produces `sandbox-lambda` Docker container image
- Acceptance criteria:
  - Docker container compiles/runs user code snippets in Python and Node.js.
  - Code outputs execution logs and test assertions in JSON format.
- Verification: `docker build -t sandbox-lambda sandbox-lambda/`
- Dependencies: Task 1.2

### [ ] Task 3.2: FastAPI Local Sandbox Executor Service
- Scope: M
- Files: `backend/app/services/executor.py` (create), `backend/tests/test_executor.py` (create)
- Interfaces:
  - produces `execute_code_locally(code: str, language: str, test_suite: str) -> dict[str, Union[str, bool, list[dict[str, str]]]]` (returns `{"stdout": str, "stderr": str, "passed": bool, "test_results": list}`)
- Acceptance criteria:
  - Docker sandbox executes code, restricting runtime to 5 seconds and blocking network access.
  - Executor correctly parses execution results and handles infinite loops or security blocks.
- Verification: `pytest backend/tests/test_executor.py`
- Dependencies: Task 3.1

### Checkpoint — Phase 3
- [ ] Local Docker-based executor can run Python and Node.js code securely within local boundaries.
- Verification: `pytest backend/tests/test_executor.py` passes successfully.

---

## Plan Code Review
- [ ] Feature plan code review passed
