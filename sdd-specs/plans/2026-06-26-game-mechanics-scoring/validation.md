# Validation: Core Game Mechanics & Scoring

## Acceptance Criteria

For behavioral criteria, prefer Given/When/Then:
- [ ] Given a user who has not played today, when they start a session, then the session is initialized, and their daily game count is set to 1.
- [ ] Given a user who has already played today, when they attempt to start a session, then they receive an HTTP 400 Bad Request with a daily cap message.
- [ ] Given a player starts a session, when the session is created, then a 30-minute timer ticks down, and automatically submits the current code at 0 remaining seconds.
- [ ] Given a solution submission, when the workspace is checked, then it is validated to ensure it is a single-file submission matching Python or Node.js/TypeScript.
- [ ] Given LLM requests via proxy, when the token budget is reached, then any further requests are blocked with HTTP 429 Too Many Requests.
- [ ] Given a completed game session, when scores are calculated, then the total score is computed as the average of the correctness (tests passed), efficiency (unused token budget), and speed (unused time) scores.

## Test Coverage
- [ ] Unit tests pass for new logic (deps, game sessions, scoring calculations, LLM proxy checks)
- [ ] Integration tests pass (verifying profile updates against a simulated database instance)
- [ ] E2E covers critical path (Auth -> Start challenge -> Submit -> Scorecard shown)

## Automation Checks
- [ ] `make lint` runs and passes with no ruff or TypeScript linting errors
- [ ] `make test` runs and all tests pass

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked
- No regressions in existing tests
- Code review approved
