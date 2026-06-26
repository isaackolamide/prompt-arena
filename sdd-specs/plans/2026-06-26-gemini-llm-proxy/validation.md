# Validation: gemini-llm-proxy

## Acceptance Criteria

### Behavioral Criteria
- [ ] Given a POST request to `/challenges/session/{session_id}/prompt` with payload `{ "prompt": "..." }`, When the session state is checked in Supabase and found to be inactive or expired, Then return a `403 Forbidden` response (`"Active session not found"`).
- [ ] Given a POST request to `/challenges/session/{session_id}/prompt`, When the session's remaining token budget is <= 0, Then return a `403 Forbidden` response (`"Token budget exhausted"`) immediately without calling the Gemini API.
- [ ] Given a POST request to `/challenges/session/{session_id}/prompt`, When the prompt length is greater than 10,000 characters, Then return a `400 Bad Request` validation error.
- [ ] Given a POST request to `/challenges/session/{session_id}/prompt` that passes validation, When Gemini API invocation succeeds, Then deduct total tokens atomically from `game_sessions.token_budget` in Supabase using the database engine, and return `{ "response": str, "tokens_used": int, "remaining_budget": int }`.
- [ ] Given a slow or hanging upstream Gemini API request, When the call exceeds 10 seconds, Then terminate the request and return a `504 Gateway Timeout` error.
- [ ] Given an upstream Gemini API error:
  - When the Gemini API returns a rate limit error (`429`), Then return a standard HTTP `429 Too Many Requests` status with a descriptive message.
  - When any other Gemini API failure occurs, Then return an HTTP `502 Bad Gateway` error and ensure no tokens are deducted from the player's budget.

### Security Criteria
- [ ] Verify FastAPI proxy endpoints strictly require active authentication headers (verifying Supabase Auth bearer tokens matching the active player session owner).
- [ ] Verify `GEMINI_API_KEY` is never exposed or returned to the client in response headers, body, or backend application logs.

## Test Coverage
- [ ] Unit tests cover prompt validation rules and error mappings (`backend/tests/unit/test_llm_proxy_service.py`).
- [ ] Unit tests cover authentication guard logic (`backend/tests/unit/test_auth_guard.py`).
- [ ] Integration tests verify the Supabase stored function atomic subtraction behavior (`backend/tests/integration/test_database_budget.py`).
- [ ] Integration tests verify the complete FastAPI endpoint flow, using mocked Gemini API responses (`backend/tests/integration/test_challenges_api.py`).
- [ ] Overall test coverage target for new backend modules is >= 80%.

## Automation Checks
- [ ] Code is linted cleanly with Ruff: `make lint`
- [ ] All pytest suites pass: `make test`

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked.
- No regressions are introduced in existing tests.
- Code review is approved.
