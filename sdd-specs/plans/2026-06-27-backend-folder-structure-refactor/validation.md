# Validation: Backend Folder Structure Refactor

## Acceptance Criteria

- [x] Given the new backend structure, When we import validation schemas, Then `MagicLinkRequest`, `MagicLinkResponse`, `VerifyRequest`, and `VerifyResponse` resolve from `app.schemas.auth`.
- [x] Given the FastAPI app running locally, When API endpoints `/api/auth/magic-link` and `/api/auth/verify` are hit, Then the backend handles them properly using the migrated validation schemas.
- [x] Given the test suite is executed, When running `make test`, Then all test files compile and execute with 100% success.
- [x] Given the backend codebase, When linting checks are executed via `make lint`, Then no ruff lint or formatting errors are detected.
- [x] Given the refactored project structure, When checking `sdd-specs/tech-stack.md`, Then the documented project structure matches the actual directories.

## Test Coverage
- [x] Pytest unit and integration tests run successfully and maintain coverage of the refactored modules.
- [x] All tests mock external connections appropriately using builder patterns.

## Automation Checks
- [x] Running `make lint` runs with zero warnings or errors.
- [x] Running `make test` outputs a fully clean test run.

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked.
- No regressions exist in unit, integration, or E2E tests.
- Code review approved.
