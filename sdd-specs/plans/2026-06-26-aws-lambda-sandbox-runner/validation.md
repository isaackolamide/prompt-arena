# Validation: 2026-06-26-aws-lambda-sandbox-runner

## Acceptance Criteria

### Behavioral Criteria
- [x] Given a test execution request from the FastAPI backend, When the AWS Lambda function is invoked, Then it accepts a payload containing the player's single-file source code, the target language environment (Python or Node/TypeScript), and the challenge test suite.
- [x] Given code execution inside AWS Lambda, When running, Then the execution environment is strictly isolated within a Firecracker microVM with outbound network access fully disabled.
- [x] Given a player code submission execution, When it exceeds a strict 5-second timeout, Then the run is immediately terminated and a timeout failure is returned to the caller.
- [x] Given a completed execution run, When finished, Then the sandbox safely extracts, formats, and returns the standard output (`stdout`), standard error (`stderr`), and a structured JSON result indicating which unit tests passed/failed.
- [x] Given player code submissions containing network requests (e.g. calling external HTTP endpoints), When executed in the sandbox, Then the network requests are blocked and fail to execute.
- [x] Given infinite loop submissions (e.g. `while True: pass`), When executed in the sandbox, Then the run is terminated precisely at 5 seconds and returns a timeout status.
- [x] Given standard unit test execution results, When returned, Then they are correctly parsed back to the caller in less than 2 seconds (excluding cold start latency).

### Security & Telemetry Criteria
- [x] Verify that player submissions are never run directly on the FastAPI API backend container.
- [x] Verify that AWS access credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are kept isolated and are never returned in response payloads or emitted in logs.
- [x] Verify that structured logging events (`sandbox_run_started`, `sandbox_run_completed`, `sandbox_run_failed`) are logged to standard output for log ingestion.

## Test Coverage
- [x] Unit tests cover Python/Node handler routing logic in `sandbox-lambda/test_runner.py`.
- [x] Unit tests cover settings configuration load logic in `backend/tests/unit/test_config.py` (or similar).
- [x] Unit tests cover backend client invocation, payload serialization, timeout parsing, and custom error translation in `backend/tests/unit/test_lambda_client.py`.
- [x] Overall test coverage target for new backend/sandbox modules is >= 80%.

## Automation Checks
- [x] Code is linted cleanly: `make lint`
- [x] All unit and integration test suites pass: `make test`
- [x] AWS CDK Stack synthesizes cleanly without TypeScript compilation errors: `cd infra && npx cdk synth`

## Definition of Done

This feature is mergeable when:
- All acceptance criteria above are checked.
- No regressions are introduced in existing test suites.
- Code review is approved.
