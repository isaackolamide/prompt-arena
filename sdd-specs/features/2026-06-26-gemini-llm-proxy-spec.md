# Feature Spec: Gemini LLM Proxy

## Objective
Design and implement a secure, rate-limited, and token-metered backend proxy for Google Gemini API calls. The proxy interceptor enforces game session-bound token budgets for players prompting LLMs within the arena workspace and prevents custom client-supplied keys or API cost overruns.

## User & Stakeholder
- **Invited Software Engineer (Player)**: Wants to issue prompts to Gemini in the coding terminal workspace and get rapid responses within a strict token budget.
- **System Administrator**: Requires absolute key security, accurate token usage tracking in Supabase, and budget limits to keep costs low and scoring fair.

## Acceptance Criteria
- **Given** a POST request to `/challenges/session/{session_id}/prompt` with a payload of `{ "prompt": "..." }`:
  - **When** the session state is checked in Supabase and found to be inactive or expired, **then** return a `403 Forbidden` response (`"Active session not found"`).
  - **When** the session's remaining token budget is $\le 0$, **then** return a `403 Forbidden` response (`"Token budget exhausted"`) immediately without calling Gemini.
  - **When** the prompt length is greater than 10,000 characters, **then** return a `400 Bad Request` validation error.
  - **When** validation passes, **then** invoke the Google Gemini API (model `gemini-1.5-flash`) using the server-side API key.
- **Given** a successful Gemini API invocation:
  - **When** the response metadata (`usage_metadata`) contains the token usage counts, **then**:
    - Deduct the total tokens (input prompt tokens + output candidate tokens) from the `game_sessions.token_budget` in the Supabase database.
    - Perform the database update using an atomic transaction query (e.g., `UPDATE game_sessions SET token_budget = token_budget - :tokens WHERE id = :id AND token_budget >= :tokens`) to prevent concurrent query race conditions.
    - Return a JSON response containing `{ "response": str, "tokens_used": int, "remaining_budget": int }`.
- **Given** a slow or hanging upstream Gemini API request:
  - **When** the request exceeds a strict 10-second timeout, **then** terminate the API call and return a `504 Gateway Timeout` error.
- **Given** upstream Gemini API failures:
  - **When** the Gemini API returns a rate limit error (`429`), **then** return a standard HTTP `429 Too Many Requests` status to the client with a descriptive message.
  - **When** any other Gemini API failure occurs, **then** return an HTTP `502 Bad Gateway` error and ensure no tokens are deducted from the player's budget.

## Technical Constraints
- The FastAPI proxy endpoints must strictly require active authentication headers (verifying Supabase Auth bearer tokens matching the active player session owner).
- Only text-to-text completions are supported (multimodal inputs are disallowed).
- The `GEMINI_API_KEY` must never be exposed or returned to the client in headers, body, or logs.
- Token tracking must rely on the official `usage_metadata` object returned by the Google Generative AI Python SDK.
- The subtraction statement must execute atomically on the database engine.
- Unit and integration tests for the proxy must be implemented in the `backend/tests/` directory, mocking the Gemini client API using standard builders.

## In Scope
- FastAPI router logic and request models under `backend/app/routes/challenges.py` (or corresponding module).
- Integration with the official `google-generativeai` Python SDK library.
- Supabase/PostgreSQL database update query executing atomic subtraction.
- Injected system prompts guiding Gemini's persona to avoid giving direct challenge solutions.
- Comprehensive unit and integration test suite targeting the `/prompt` endpoint and budget validation helper functions.

## Out of Scope
- Frontend Monaco Editor UI workspace integration (defined in `sdd-specs/features/2026-06-26-game-session-workspace-spec.md`).
- React terminal simulated console UI widgets (defined in `sdd-specs/features/2026-06-26-game-session-workspace-spec.md`).
- Persistent storage of the prompt/response text history inside the database.
- Prompt caching or embedding retrieval.

## Dependencies
- Supabase database connection and game sessions tables (defined in Phase 1 database setup).
- Upstream Google Gemini API key credentials and access.

## Stakeholder Flags
- **Prompt Guardrails**: Simple system prompt framing prevents Gemini from outputting complete refactored files directly to players. If players discover prompt-injection bypasses to copy-paste solutions, more advanced prompt filtering or post-processing parsing might be required.

## Success Metrics
- **Zero Token Leakage**: Submissions and prompts are strictly blocked when remaining session tokens reach $\le 0$.
- **100% Security**: The raw Gemini API key is never exposed via public network requests.
- **Minimal Overhead**: The database checks and updates add less than 100ms of latency per query.
