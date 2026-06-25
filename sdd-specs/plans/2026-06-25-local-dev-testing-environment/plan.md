# 2026-06-25-local-dev-testing-environment Implementation Plan

**Goal:** Establish a unified local containerized development and testing environment with automated migrations, seeds, unit/integration/E2E test runners, and sandboxed executor isolation.
**Architecture:** Use the official Supabase CLI emulator on the host machine to manage PostgreSQL database, Auth GoTrue, and API gateway services. Use a root `docker-compose.yml` to orchestrate code reload-enabled FastAPI backend and React frontend containers that connect to the host via `host.docker.internal`.
**Tech Stack:** Docker, Docker Compose, Supabase CLI, FastAPI (Python), Vite + React + TypeScript, Playwright (E2E), pytest (unit/integration), vitest (unit).

---

## Phase 1: Setup Host, Supabase CLI, and Playwright

### Task 1.1: Local Supabase CLI Initial Configuration & Migration Path
- [x] Task Completed
- Scope: S
- Files: `supabase/config.toml` (create), `supabase/migrations/20260625000000_init_schema.sql` (create), `supabase/seed.sql` (create)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given a clean environment, When running `npx supabase init`, Then the `supabase/` configuration structure is initialized.
  - Given the database schema at `backend/app/db/schema.sql`, When copied to `supabase/migrations/20260625000000_init_schema.sql`, Then it serves as the base schema for local development.
  - Given the database seeds at `supabase/seed.sql`, When local Supabase boots, Then mock challenges and profiles are seeded.
- Verification: `npx supabase db lint`
- Dependencies: none

### Task 1.2: Host Environment Bootstrapping & Setup Script
- [ ] Task Completed
- Scope: S
- Files: `Makefile` (modify)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given a new repository clone, When `make setup` is run, Then it copies `.env.example` to `.env` (if missing), installs Python backend packages via `pip3 install -r backend/requirements.txt`, and installs React frontend dependencies via `npm install` inside `frontend/`.
- Verification: Run `make setup` on a clean environment
- Dependencies: Task 1.1

### Task 1.3: Playwright Integration and Configuration
- [ ] Task Completed
- Scope: S
- Files: `frontend/package.json` (modify), `frontend/playwright.config.ts` (create), `frontend/e2e/auth.spec.ts` (create)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given the Playwright integration, When `npm install -D @playwright/test` is run (via `make setup`), Then the package is added to devDependencies and `frontend/playwright.config.ts` is configured to target `http://localhost:5173`.
  - Given the E2E test files, When `npx playwright test` is run, Then a basic smoke page load verification test passes.
- Verification: `cd frontend && npx playwright test`
- Dependencies: Task 1.2

### Checkpoint — Phase 1
- [ ] Local Supabase initialized, Playwright installed, and Makefile setup targets integrated.
- Verification: Run `make setup` and ensure all host dependencies and Playwright are installed without errors.

---

## Phase 2: Fullstack Docker Compose Orchestration

### Task 2.1: Write Root Docker Compose Configuration
- [ ] Task Completed
- Scope: M
- Files: `docker-compose.yml` (create), `backend/Dockerfile` (create), `frontend/Dockerfile` (create)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given a configured host, When running `docker compose up --build -d`, Then `backend` and `frontend` services compile and boot in containerized dev mode.
  - Given the containers are running, When requesting `http://localhost:8000/health`, Then backend returns status ok and communicates with host Supabase services via `host.docker.internal`.
- Verification: `docker compose ps` shows both services running; health check endpoint returns 200 OK.
- Dependencies: Checkpoint — Phase 1

### Task 2.2: Implement Automatic Schema/Seed Executions & Stop Target
- [ ] Task Completed
- Scope: S
- Files: `Makefile` (modify)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given the local repository, When `make start` is run, Then it executes `npx supabase start` to run DB/Auth, followed by `docker compose up -d` to run frontend/backend, applying migrations/seeds automatically.
  - Given the active containers, When `make stop` is run, Then `docker compose down` and `npx supabase stop` clean up all active containers.
- Verification: Run `make start` and verify Supabase is running on port 54321 and tables are seeded in DB; then run `make stop` and verify no containers are left.
- Dependencies: Task 2.1

### Checkpoint — Phase 2
- [ ] Local fullstack dev environment builds, starts, and tears down via single Makefile targets.
- Verification: Run `make start` followed by `make stop`.

---

## Phase 3: Automated Test Suites Integration

### Task 3.1: Unit Testing Makefile Integration
- [ ] Task Completed
- Scope: XS
- Files: `Makefile` (modify)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given a local repository, When `make test-unit` is run, Then unit tests run for backend via `pytest` (using mocked Supabase DB handler) and frontend via `vitest` (in `jsdom` mode) and exit cleanly.
- Verification: `make test-unit` exits with code 0.
- Dependencies: Checkpoint — Phase 2

### Task 3.2: Temp Integration Database Bootstrapping and Cleanup
- [ ] Task Completed
- Scope: M
- Files: `backend/tests/conftest.py` (modify), `backend/tests/integration/test_database.py` (create), `Makefile` (modify)
- Interfaces: produces `postgres_test_db() -> str` as a pytest fixture; produces `run_migrations_on_test_db(conn_str: str) -> None` to run SQL migrations; consumes none
- Acceptance criteria:
  - Given a local setup, When `make test-integration` is run, Then a temporary containerized PostgreSQL test database (using `postgres:15-alpine` or `supabase/postgres`) is programmatically booted via the python `docker` SDK.
  - Given the container is booted, When migrations are applied, Then backend integration tests run against this clean temporary database, and the container is stopped/deleted on teardown.
- Verification: `make test-integration` runs successfully and cleans up the temporary docker container.
- Dependencies: Task 3.1

### Task 3.3: Playwright E2E Test Suite targeting Compose Frontend
- [ ] Task Completed
- Scope: S
- Files: `frontend/e2e/auth.spec.ts` (modify), `Makefile` (modify)
- Interfaces: produces none; consumes none
- Acceptance criteria:
  - Given `make test-e2e` is run, When the compose frontend service is active, Then Playwright E2E tests run targeting `http://localhost:5173`, verifying user registration and login flows.
- Verification: `make test-e2e` executes and all tests pass.
- Dependencies: Task 3.2

### Checkpoint — Phase 3
- [ ] All test levels (unit, integration, and E2E) run and pass successfully in local isolation.
- Verification: Run `make test-unit`, `make test-integration`, and `make test-e2e` sequentially.

---

## Plan Code Review
- [ ] Feature plan code review passed
