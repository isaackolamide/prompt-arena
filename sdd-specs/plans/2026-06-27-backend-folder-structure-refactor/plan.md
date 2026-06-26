# Backend Folder Structure Refactor Implementation Plan

**Goal:** Refactor the FastAPI backend codebase into a simplified, layer-based directory structure to reduce imports/dependency boilerplate while ensuring type safety and linter cleanliness.
**Architecture:** Restructure `backend/app/` to use simplified conceptual layers (`api/`, `core/`, `db/`, `schemas/`, `services/`). Extract schemas from `api/auth.py` to `schemas/auth.py`, align Python package imports in the backend code and pytest suites, and run comprehensive test/lint verifications.
**Tech Stack:** Python 3.11+, FastAPI, Pydantic, pytest.

---

## Phase 1: Reorganization & Package Layout

### Task 1.1: Create Schemas Package & Move Auth Schemas
- [x] Task Completed
- Scope: S
- Files: `backend/app/schemas/__init__.py` (create), `backend/app/schemas/auth.py` (create), `backend/app/api/auth.py` (modify)
- Interfaces:
  - produces class `MagicLinkRequest(BaseModel)`
  - produces class `MagicLinkResponse(BaseModel)`
  - produces class `VerifyRequest(BaseModel)`
  - produces class `VerifyResponse(BaseModel)`
- Acceptance criteria:
  - Given the schemas package, When checking validation rules, Then they strictly validate:
    * `MagicLinkRequest.email`: `EmailStr`
    * `MagicLinkResponse.status`: `str`
    * `VerifyRequest.email`: `EmailStr`
    * `VerifyRequest.token`: `str`
    * `VerifyResponse.access_token`: `str`
- Verification: Run `python -c "from app.schemas.auth import MagicLinkRequest"` from the backend directory to verify it resolves cleanly.
- Dependencies: none

### Checkpoint — Phase 1
- [x] Schemas package is successfully created and imports execute cleanly.
- Verification: `python -c "from app.schemas.auth import MagicLinkRequest"`

---

## Phase 2: Imports & References Update

### Task 2.1: Update Backend App Imports
- [x] Task Completed
- Scope: S
- Files: `backend/app/api/auth.py` (modify)
- Interfaces:
  - consumes `MagicLinkRequest`, `MagicLinkResponse`, `VerifyRequest`, `VerifyResponse` from `app.schemas.auth`
- Acceptance criteria:
  - Given the FastAPI application, When auth routes are hit, Then the server uses schemas imported from `app.schemas.auth` and preserves existing API behaviors.
- Verification: Run ruff check on the modified auth file.
- Dependencies: Task 1.1

### Task 2.2: Update Backend Test Suite Imports
- [x] Task Completed
- Scope: S
- Files: `backend/tests/test_auth.py` (modify), `backend/tests/test_executor.py` (modify)
- Interfaces:
  - consumes `execute_code_locally` from `app.services.executor` (standardizes import in `test_executor.py` from `backend.app.services.executor` to `app.services.executor`)
- Acceptance criteria:
  - Given backend test execution, When `make test` is run, Then all test files compile and execute successfully.
- Verification: `make test`
- Dependencies: Task 2.1

### Task 2.3: Verification, Clean Up & Linting
- [x] Task Completed
- Scope: XS
- Files: none
- Interfaces: none
- Acceptance criteria:
  - Given the refactored directory structure, When linting and formatting is run, Then all checks pass with 100% success.
- Verification: `make lint` and `make test`
- Dependencies: Task 2.2

### Checkpoint — Phase 2
- [x] All backend test suites pass and formatting/linting checkers compile cleanly.
- Verification: `make lint && make test`

---

## Plan Code Review
- [x] Feature plan code review passed
