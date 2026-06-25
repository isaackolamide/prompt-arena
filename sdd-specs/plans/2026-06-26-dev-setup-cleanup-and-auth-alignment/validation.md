# Validation: dev-setup-cleanup-and-auth-alignment

## Acceptance Criteria

- [x] Given the developer runs `make start`, When the Supabase local emulator starts, Then only the essential containers (`db`, `api`, `auth`, `local_smtp`, `studio`, `kong`) are launched, and `realtime`, `storage`, `imgproxy`, and `edge-runtime` containers are not spawned.
- [x] Given a player visiting the homepage, When they see the sign-in container, Then they see a dark glassmorphic card with subtle borders, glowing focus inputs, responsive design, and smooth transitions.
- [x] Given a player enters their email and submits the form, When they click "Send OTP", Then the backend issues an OTP code, logs the action with a masked email, and the frontend transitions to the verification input screen.
- [x] Given the player retrieves the OTP code from the local Inbucket console, When they enter the code and submit, Then they are authenticated, their profile is initialized/returned, and the dashboard welcome screen is rendered.
- [x] Given the backend codebase, When we inspect `backend/app/api/auth.py`, Then the password endpoints `/register` and `/login` are completely removed.

## Test Coverage

- [x] Unit tests pass for magic link request and OTP verification endpoints (`pytest backend/tests/`).
- [x] E2E Playwright tests cover the full OTP login scenario from landing screen to dashboard access (`make test-e2e`).
- [x] Code coverage for backend auth handlers is maintained at or above 80%.

## Automation Checks

- [x] TypeScript linter checks clean with no errors or warnings (`cd frontend && npm run lint`).
- [x] Vite production build compiles successfully with no TypeScript errors or typing escapes (`cd frontend && npm run build`).
- [x] Backend code passes formatting and linting rules (`make lint`).

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked.
- No regressions in existing backend or frontend test suites.
- All code files pass the formatting, linting, and type-checking checks.
- Code review approved.
