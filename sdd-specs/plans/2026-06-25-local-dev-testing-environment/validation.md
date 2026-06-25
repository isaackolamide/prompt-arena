# Validation: 2026-06-25-local-dev-testing-environment

## Acceptance Criteria

For behavioral criteria, prefer Given/When/Then:
- [ ] Given a new developer checkout, When `make setup` is run, Then host-level dependencies (npm, pip), `.env` templates, and Playwright browsers are installed and configured.
- [ ] Given a configured host, When `make start` is run, Then the React frontend, FastAPI backend, and Supabase CLI emulator services build and run in Docker compose, and database migrations/seeds are executed automatically.
- [ ] Given a running local environment, When `make test-unit` is run, Then unit tests run for backend via `pytest` (using mocked database handlers) and frontend via `vitest` (in `jsdom` mode) and exit cleanly.
- [ ] Given a local setup, When `make test-integration` is run, Then a temporary containerized PostgreSQL/Supabase test database is booted, migrations are run, backend integration tests execute, and the container is torn down.
- [ ] Given a running local environment, When `make test-e2e` is run, Then Playwright runs end-to-end tests targeting the containerized frontend URL.
- [ ] Given a running local sandbox execution container, When executing user-submitted code snippets, Then the executor has no network or database access and cannot access the host.

## Test Coverage
- [ ] Unit tests pass for new logic, achieving at least 80% coverage for modified files.
- [ ] Integration tests verify real PostgreSQL client operations against the temporary container.
- [ ] E2E covers critical path registration, login, and simple frontend routing targeting `http://localhost:5173`.

## Automation Checks
- [ ] Root `Makefile` targets successfully execute without requiring manual arguments.
- [ ] Git-ignored files (`.env`, `supabase/.temp/`) are not committed.
- [ ] `make lint` passes ruff and typescript checks with zero warnings/errors.

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked
- No regressions in existing tests
- Code review approved
