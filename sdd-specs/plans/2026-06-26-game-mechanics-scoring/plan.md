# Core Game Mechanics & Scoring Implementation Plan

**Goal:** Implement session boundaries, daily gameplay caps, LLM budget controls, and score calculations.
**Architecture:** Use FastAPI backend dependencies for authentication and state verification, updating profile metadata using a Supabase admin client to bypass row level security limits. On the frontend, a custom React hook manages the count-down timer and triggers auto-submissions.
**Tech Stack:** FastAPI (Python), Vite + React/TypeScript, Supabase.

---

## Phase 1: Backend Game Session Lifecycle & Enforcements

### Task 1.1: Authentication Dependency Helper
- [ ] Task Completed
- Scope: S
- Files: `backend/app/api/deps.py` (create)
- Interfaces:
  - Produces: `get_current_profile(authorization: str = Header(...)) -> dict[str, Union[str, int, None]]` (Retrieves the user's Profile record using Supabase JWT token)
- Acceptance criteria:
  - Given a valid JWT auth token, retrieves the profile from `public.profiles`.
  - Given an invalid/expired token or missing header, raises HTTP 401 Unauthorized.
- Verification: `pytest backend/tests/test_deps.py`
- Dependencies: none

### Task 1.2: Start Game Session with Daily Cap Check
- [ ] Task Completed
- Scope: M
- Files: `backend/app/api/game.py` (create), `backend/app/main.py` (modify)
- Interfaces:
  - Produces: `start_game_session(challenge_id: str, profile: dict = Depends(get_current_profile)) -> dict[str, Union[str, None]]`
- Acceptance criteria:
  - Given a player with daily count < 1, starting a session inserts a new session with `status='in_progress'`, increments `daily_game_count` in their profile, and updates `last_game_played_at`.
  - Given a player who has already played today, starting a session returns HTTP 400 Bad Request.
  - Updates to the profile are executed via `get_supabase_admin_client()` to bypass the tampering prevention database triggers.
- Verification: `pytest backend/tests/test_game.py`
- Dependencies: Task 1.1

### Task 1.3: Submit Solution & Scorecard Generation
- [ ] Task Completed
- Scope: M
- Files: `backend/app/api/game.py` (modify), `backend/app/services/scoring.py` (create)
- Interfaces:
  - Produces: `calculate_scores(correctness_passed: int, correctness_total: int, token_budget: int, tokens_used: int, elapsed_seconds: float) -> dict[str, float]`
  - Produces: `submit_game_session(session_id: str, code: str, profile: dict = Depends(get_current_profile)) -> dict[str, Union[str, float, dict, None]]`
- Acceptance criteria:
  - Given a solution submission, validates that it contains a single file in a supported language (Python, Node.js/TypeScript).
  - Evaluates code by invoking the sandbox executor, calculating correctness, efficiency, and speed.
  - Saves the scorecard, sets session status to `'completed'`, and returns the scorecard detail.
- Verification: `pytest backend/tests/test_game.py`
- Dependencies: Task 1.2

### Task 1.4: LLM Proxy Token Budget tracking and enforcement
- [ ] Task Completed
- Scope: M
- Files: `backend/app/api/proxy.py` (create), `backend/app/main.py` (modify)
- Interfaces:
  - Produces: `proxy_llm_request(session_id: str, prompt: str, profile: dict = Depends(get_current_profile)) -> dict[str, Union[str, int]]`
- Acceptance criteria:
  - Tracks and accumulates the input/output tokens used in the current session.
  - If token budget is exceeded, blocks further requests with HTTP 429 Too Many Requests.
- Verification: `pytest backend/tests/test_proxy.py`
- Dependencies: Task 1.2

### Checkpoint — Phase 1
- [ ] All backend logic endpoints verify user limits, sandbox evaluation, scoring calculation, and proxy tracking successfully.
- Verification: `make test`

---

## Phase 2: Frontend Integration & Session Timer

### Task 2.1: React Context / API Client Hook for Game Session
- [ ] Task Completed
- Scope: S
- Files: `frontend/src/hooks/useGameSession.ts` (create)
- Interfaces:
  - Produces: `useGameSession(challengeId: string) -> { session: GameSession | null, scorecard: Scorecard | null, startSession: () => Promise<void>, submitSession: (code: string) => Promise<void>, timeRemaining: number }`
- Acceptance criteria:
  - Coordinates starting and submitting the game session using backend APIs.
  - Manages countdown timer starting at 30 minutes (1800 seconds) and ticking down every second.
  - Automatically invokes submission when time hits zero.
- Verification: `vitest frontend/src/tests/useGameSession.test.ts`
- Dependencies: Task 1.3

### Task 2.2: Workspace Interface & Editor Hookup
- [ ] Task Completed
- Scope: M
- Files: `frontend/src/components/Workspace.tsx` (modify)
- Interfaces:
  - Produces: `Workspace(props: WorkspaceProps) -> JSX.Element`
- Acceptance criteria:
  - Disables Monaco editor and shows an overlay/error when daily cap is exceeded.
  - Renders side-by-side Monaco editor and simulated terminal component.
  - Displays session count-down timer, disabling components during execution and submission.
- Verification: `vitest frontend/src/tests/Workspace.test.tsx`
- Dependencies: Task 2.1

### Checkpoint — Phase 2
- [ ] Frontend builds without TypeScript or bundling errors, and all interface tests pass successfully.
- Verification: `npm run lint && npm run test` inside the frontend directory.

---

## Plan Code Review
- [ ] Feature plan code review passed
