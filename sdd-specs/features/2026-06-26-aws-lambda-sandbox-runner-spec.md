# Feature Spec: AWS Lambda Sandbox Runner

## Objective
Design and implement a highly secure, isolated, and timed remote code execution sandbox using AWS Lambda (Firecracker microVMs) to execute single-file Python and Node.js/TypeScript player submissions against test suites.

## User & Stakeholder
Invited and authenticated software engineers (players) who expect rapid feedback on their test executions, and system administrators who require absolute backend security, resource isolation, and protection against malicious code execution.

## Acceptance Criteria
- Given a test execution request from the FastAPI backend, when the AWS Lambda function is invoked, then it accepts a payload containing the player's single-file source code, the target language environment (Python or Node/TypeScript), and the challenge test suite.
- Given code execution inside AWS Lambda, when running, then the environment is isolated within a Firecracker microVM with outbound network access fully disabled.
- Given a player code submission execution, when it exceeds a strict 5-second timeout, then the run is immediately terminated and a timeout failure is returned to the caller.
- Given a completed execution run, when finished, then the sandbox safely extracts, formats, and returns the standard output (`stdout`), standard error (`stderr`), and a structured JSON result indicating which unit tests passed/failed.

## Technical Constraints
- Submission executions must never run directly on the API backend container (must go to AWS Lambda).
- Outbound network access must be blocked at the execution level (e.g. via Lambda VPC settings, routing configuration, or IAM/execution policies).
- Maximum execution time limit is strictly capped at 5 seconds.
- Supported runtimes: Python (latest 3.x) and Node.js/TypeScript (latest LTS).
- Must return test results in a standardized JSON payload format (e.g. `{ "passed": int, "total": int, "tests": [ { "name": str, "status": "pass"|"fail", "message": str } ] }`).
- Unit and integration tests for the sandbox runner wrapper must be implemented in the `sandbox-lambda/` test directory.

## In Scope
- Deployment configuration and Dockerfile/Zip packaging scripts for building the AWS Lambda execution images.
- Script runners inside AWS Lambda for running `pytest` (for Python challenges) and `vitest`/`jest` (for Node/TS challenges) dynamically against raw string code inputs.
- Outbound network traffic filtering/blocking infrastructure configurations (e.g. VPC private subnets without NAT Gateway routes, or Lambda-specific system policy rules).
- FastAPI backend client class (`LambdaClient`) responsible for AWS SDK (Boto3) integration and payload handoff.
- Standardized parser scripts to capture console output and structure test framework exit codes/logs into clean JSON response format.
- option to either use CDK or Terraform to create lambda (please recommend one and justify your choice but I have to confirm it).

## Out of Scope
- Frontend Monaco editor visual layout and UI console terminal components (defined in the workspace specs).
- Frontend websocket/polling transport implementation (defined in the workspace specs).
- Gemini LLM proxy routing and prompt checking configurations.

## Dependencies
- AWS IAM Roles and Lambda execution environment provisioning.
- FastAPI backend credentials for invoking AWS Lambda (AWS Access Key ID, Secret Access Key, and Lambda Endpoint/Region variables).

## Stakeholder Flags
- **Cold Starts**: AWS Lambda cold starts might impact response time during the first test execution. Pre-warming strategies or keeping functions warm (Provisioned Concurrency) can be explored if cold starts exceed acceptable limits, but requires stakeholder cost approval.

## Success Metrics
- Player code submissions containing network requests (e.g. calling external HTTP endpoints) are blocked and fail to execute.
- Infinite loop submissions (e.g. `while True: pass`) are terminated precisely at 5 seconds.
- Standard unit test execution results are correctly returned and parsed back to the caller in less than 2 seconds (excluding cold start latency).
