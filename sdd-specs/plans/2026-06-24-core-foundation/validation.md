# Validation: core-foundation

## Acceptance Criteria

### Monorepo Setup & Testing
- [x] Given a clean workspace, when running `make build`, then project directories are generated and environment configurations are set.
- [x] Given a clean workspace, when running `make test`, then both pytest (backend) and vitest (frontend) suites run and succeed.

### Database Schema
- [x] Given a Postgres database, when schema script is executed, then tables for `profiles`, `challenges`, `game_sessions`, and `scorecards` are created with correct relational keys.

### Authentication & API Boilerplate
- [x] Given a valid email address, when POSTing to `/api/auth/magic-link`, then the server requests Supabase Auth to send a magic link.
- [x] Given a valid email and OTP token, when POSTing to `/api/auth/verify`, then the server returns an access token and user information.

### Local Sandbox Executor
- [x] Given a valid python/javascript code snippet, when executed, then the local Docker executor compiles, runs, and returns test results JSON.
- [x] Given an infinite loop snippet, when executed, then the container execution times out at 5 seconds and returns a timeout error.
- [x] Given a snippet attempting network connection, when executed, then the execution fails due to disabled network capabilities.

## Test Coverage
- [x] Unit tests pass for new logic
- [x] Integration tests pass
- [x] Test coverage target of 80% is met on backend auth & executor modules.

## Automation Checks
- [x] `make lint` executes successfully with no lint or type-checking errors.
- [x] `make test` runs and all tests pass.

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked
- No regressions in existing tests
- Code review approved
