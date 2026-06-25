# dev-setup-cleanup-and-auth-alignment Implementation Plan

**Goal:** Optimize local development container footprints by disabling unused services and align the user interface with the Magic Link/OTP email authentication flow under a high-fidelity glassmorphic visual style.
**Architecture:** Disable realtime, storage, and edge-runtime in `supabase/config.toml`. Remove legacy password routes and endpoints on FastAPI (`backend/app/api/auth.py`). Refactor `frontend/src/App.tsx` to handle state-driven OTP request/verify screens styled with dark-mode glassmorphic CSS, and write pytest and Playwright tests to secure the flows.
**Tech Stack:** Supabase Local Emulator, Python FastAPI, React/TypeScript/Vite.

---

## Phase 1: Config Optimization & Backend Cleanup

### Task 1.1: Optimize Supabase Config
- [x] Task Completed
- Scope: XS
- Files: `supabase/config.toml` (modify)
- Interfaces: none (configuration only)
- Acceptance criteria:
  - Given the developer starts the environment, When `make start` is executed, Then only the Postgres db, auth, PostgREST api, local SMTP (Inbucket), studio, and kong gateway containers are spawned, and no realtime/storage/functions run.
- Verification: Run `make stop && make start` and check active docker containers using `docker ps`.
- Dependencies: none

### Task 1.2: Remove Password-Based Backend Routes
- [x] Task Completed
- Scope: S
- Files: `backend/app/api/auth.py` (modify)
- Interfaces:
  - Removes: `post_register(payload: RegisterRequest) -> dict[str, str]`
  - Removes: `post_login(payload: LoginRequest) -> dict[str, str]`
- Acceptance criteria:
  - Given the API is running, When an HTTP POST is made to `/api/auth/register` or `/api/auth/login`, Then the server returns 404 Not Found.
- Verification: Run `make test` to verify no compile/syntax errors exist on the backend.
- Dependencies: none

### Task 1.3: Backend Auth Route Verification
- [x] Task Completed
- Scope: S
- Files: `backend/tests/test_auth.py` (modify)
- Interfaces:
  - produces `test_magic_link_request(client: TestClient)`
  - produces `test_otp_verification(client: TestClient)`
- Acceptance criteria:
  - Given the pytest suite is run, When checking the API auth routes, Then OTP magic links request and verification tests pass successfully.
- Verification: `pytest backend/tests/`
- Dependencies: Task 1.2

### Checkpoint — Phase 1
- [x] Supabase CLI runs with minimal container footprint and FastAPI has deprecated password registration.
- Verification: `docker ps --format "table {{.Names}}" && pytest backend/`

---

## Phase 2: Frontend Auth Alignment & Premium UI/UX

### Task 2.1: Frontend Auth State and API Logic
- [ ] Task Completed
- Scope: M
- Files: `frontend/src/App.tsx` (modify)
- Interfaces:
  - produces `handleRequestOtp(email: string): Promise<void>`
  - produces `handleVerifyOtp(email: string, token: string): Promise<void>`
  - consumes `POST /api/auth/magic-link`
  - consumes `POST /api/auth/verify`
- Acceptance criteria:
  - Given a player inputting their email, When they submit, Then the frontend triggers `/api/auth/magic-link` and transitions to the OTP entry screen.
  - Given the verification screen, When the player enters the OTP and submits, Then the client verifies it via `/api/auth/verify` and displays the authenticated welcome dashboard.
- Verification: Build the frontend with `cd frontend && npm run build` (confirming no TypeScript errors or `any` type escapes).
- Dependencies: Task 1.2

### Task 2.2: Premium Glassmorphism UI Styles
- [ ] Task Completed
- Scope: M
- Files: `frontend/src/App.tsx` (modify)
- Interfaces: none (CSS / DOM updates)
- Acceptance criteria:
  - Given a player rendering the landing page, When viewed in a browser, Then the form card features a semi-transparent glassmorphic background, glowing border boundaries, Inter/Outfit typography, clean spacing, and micro-animated interactive feedback states.
- Verification: Inspect the interface visually in a browser to check alignment, animations, and typography.
- Dependencies: Task 2.1

### Task 2.3: End-to-End Authentication Tests
- [ ] Task Completed
- Scope: S
- Files: `frontend/e2e/auth.spec.ts` (create)
- Interfaces: none (E2E test suite)
- Acceptance criteria:
  - Given the E2E playwright runner, When executing the auth test suite, Then a player can enter their email, submit, verify the OTP mock, and reach the home dashboard.
- Verification: `cd frontend && npx playwright test`
- Dependencies: Task 2.2

### Checkpoint — Phase 2
- [ ] React frontend compiles cleanly with no warning alerts, shows premium glassmorphism layouts, and E2E authentication passes.
- Verification: `cd frontend && npm run build && npx playwright test`

---

## Plan Code Review
- [ ] Feature plan code review passed
