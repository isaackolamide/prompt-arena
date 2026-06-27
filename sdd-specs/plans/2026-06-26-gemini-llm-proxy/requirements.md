# Feature Requirements: gemini-llm-proxy

## Scope

In scope:
- FastAPI router logic and request/response models under `backend/app/api/challenges.py` and `backend/app/schemas/challenges.py`.
- Integration with the official `google-generativeai` Python SDK library.
- Supabase/PostgreSQL database migration and queries executing atomic token subtraction on the database engine.
- System prompt injection wrapper guiding Gemini's persona to avoid giving direct challenge solutions.
- Unit and integration tests in the `backend/tests/` directory mocking the Gemini API and testing budget limits, authentication, timeouts, and error mappings.

Out of scope:
- Frontend Monaco Editor UI workspace integration (defined in `sdd-specs/features/2026-06-26-game-session-workspace-spec.md`).
- React terminal simulated console UI widgets (defined in `sdd-specs/features/2026-06-26-game-session-workspace-spec.md`).
- Persistent storage of the prompt/response text history in the database.
- Prompt caching or embedding retrieval.

## Decisions

Key technical decisions made:
- **Database Atomic Decrement**: Use a PL/pgSQL stored function `deduct_session_budget` called via Supabase RPC to decrement session token budgets atomically. This prevents concurrency race conditions (TOCTOU). See [ADR-002](sdd-specs/docs/decisions/ADR-002-atomic-token-deduction-strategy.md) for details.
- **Strict Network Timeouts**: Wrap upstream Gemini API calls with a strict 10-second request timeout using `asyncio.wait_for` to prevent hanging backend requests from exhausting client connections.
- **Client Key Isolation**: Only use the server-side `GEMINI_API_KEY` loaded via backend configurations. Never expose this key to client responses or write it to logs.
- **Development Key Fallback**: If `GEMINI_API_KEY` is empty, unconfigured, or set to a placeholder/dummy value, the proxy service will bypass live Gemini API requests and return a mock text response locally (using a fixed consumption count of 100 tokens), allowing local UI and feature testing without active credentials. All unit and integration tests will mock the SDK at the module boundary.

## Context

Why this feature is being built:
- To allow players in the competitive coding arena to issue prompts to Google Gemini in their simulated terminal workspace.
- To enforce a strict game-session token budget, ensuring fair scoring, cost control, and preventing abuse while avoiding raw API key exposure.

## Security Constraints

- **Active Session Authentication**: All endpoints require active authentication headers. Verify the Supabase Auth bearer token against the active player profile owning the game session.
- **Access Control checks**: Ensure the authenticated `profile_id` matches the session's `profile_id`. A player must not be allowed to prompt on behalf of another user's session.
- **Input Sanitization & Length Caps**: Validate input prompt lengths at the API boundary, rejecting prompts greater than 10,000 characters with a `400 Bad Request` validation error.
- **Secret Isolation**: Never log `GEMINI_API_KEY` or return it in headers/response payloads. Maintain strict environment configuration management.

## Telemetry & Observability

- **Structured Logging**: Emit structured JSON log events on prompt success and failure:
  - `llm_prompt_started`: Logged at the start of proxy execution containing `session_id` and `user_id`.
  - `llm_prompt_success`: Logged on successful generation containing `session_id`, `tokens_used`, and `remaining_budget`.
  - `llm_prompt_failed`: Logged on failures (timeout, rate limits, budget exhaustion) containing `session_id`, `error_type`, and `error_message`.
- **Alerting & Symptom Monitoring**:
  - Alert on sustained high upstream error rates (e.g., 502/504 errors on Gemini calls > 5% over 5 minutes).
  - Monitor frequency of `Token budget exhausted` events to track player performance and budget consumption.
- **RED Metrics**: Track endpoint rate, error classes (e.g., 429, 502, 504), and duration of the Gemini API call round-trips.

## Migration & Deprecation Plan

- **Schema Migration**:
  - Implement the migration script adding the `token_budget` column to the `game_sessions` table and creating the `deduct_session_budget` stored function.
  - The migration script will run during `supabase start` automatically.
- **Data Compatibility**:
  - For existing game sessions, default the new `token_budget` to 0. Since game sessions are ephemeral and linked to active development challenges, there is no legacy data dependency risk.
  - The backend FastAPI codebase will update to expect and query the `token_budget` column.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to (Phase 2)
- sdd-specs/features/2026-06-26-gemini-llm-proxy-spec.md — Feature Spec: Gemini LLM Proxy
- sdd-specs/docs/decisions/ADR-002-atomic-token-deduction-strategy.md — Atomic Token Deduction Strategy
- sdd-harness:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
- sdd-harness:references/clean-architecture-ddd-reference.md — Clean Architecture and DDD structural/layer rules. (Note: For Python/FastAPI, map concepts conceptually: presentation layer in `api/`, service layer in `services/`, database layer in `db/`).
