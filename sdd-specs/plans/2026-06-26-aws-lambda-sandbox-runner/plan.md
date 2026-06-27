# 2026-06-26-aws-lambda-sandbox-runner Implementation Plan

**Goal:** Build a secure, isolated, and timed remote code execution sandbox using AWS Lambda (Firecracker microVMs) to execute single-file Python and Node.js/TypeScript player submissions against unit test suites.
**Architecture:** Adapt `sandbox-lambda/runner.py` to support an AWS Lambda execution handler wrapper packaged in a custom Docker container. Create a backend `LambdaClient` using standard Boto3 SDK to synchronously invoke the function and parse the standardized unit test results. Define isolated VPC, ECR repository, and Lambda infrastructure using AWS CDK in TypeScript.
**Tech Stack:** AWS Lambda (Firecracker), Docker, Python 3.11, Node.js v22.x, AWS CDK (TypeScript), Boto3, FastAPI, pytest.

---

## Phase 1: Lambda Handler & Container Image Setup

### Task 1.1: AWS Lambda Handler in runner.py
- [x] Task Completed
- Scope: XS
- Files:
  * `sandbox-lambda/runner.py` (modify)
- Interfaces:
  * Produces: `lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]`
- Acceptance criteria:
  * Given a payload event containing `"code"`, `"test_suite"`, and `"language"`, When `lambda_handler` is invoked, Then it sets environmental configurations, calls the existing execution implementation, and returns the result dictionary.
  * Given CLI execution (`python runner.py`), When invoked from shell directly, Then it retains its original CLI argument parsing behavior for local development fallback.
- Verification: Run simulated handler run via command line execution.
- Dependencies: None

### Task 1.2: Lambda Handler Unit Tests
- [x] Task Completed
- Scope: S
- Files:
  * `sandbox-lambda/test_runner.py` (modify)
- Interfaces:
  * Produces: `test_lambda_handler_python_success() -> None`
  * Produces: `test_lambda_handler_node_success() -> None`
  * Produces: `test_lambda_handler_unsupported_language() -> None`
  * Consumes: `lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]` from Task 1.1
- Acceptance criteria:
  * Given mock events for Python/Node/invalid languages, When passed to `lambda_handler`, Then they execute and assert correct execution success/error returns.
- Verification: `pytest sandbox-lambda/test_runner.py`
- Dependencies: Task 1.1

### Task 1.3: Update Dockerfile for AWS Lambda Container Runtime
- [x] Task Completed
- Scope: S
- Files:
  * `sandbox-lambda/Dockerfile` (modify)
- Interfaces:
  * None (Container Entrypoint config)
- Acceptance criteria:
  * Given the custom Python/Node slim container image, When packaged, Then it installs `awslambdaric` and sets the container ENTRYPOINT and CMD to run the Lambda handler client.
- Verification: `docker build -t sandbox-lambda sandbox-lambda/` builds cleanly.
- Dependencies: Task 1.1

### Checkpoint — Phase 1
- [x] Sandbox Lambda container builds cleanly and all local unit tests for the Lambda handler run pass.
- Verification: Run `docker build -t sandbox-lambda sandbox-lambda/` and `pytest sandbox-lambda/test_runner.py`

---

## Phase 2: FastAPI Backend Integration

### Task 2.1: Settings and Configuration Update
- [x] Task Completed
- Scope: XS
- Files:
  * `backend/app/core/config.py` (modify)
  * `.env.example` (modify)
- Interfaces:
  * Produces: `Settings.AWS_ACCESS_KEY_ID: str`
  * Produces: `Settings.AWS_SECRET_ACCESS_KEY: str`
  * Produces: `Settings.AWS_REGION: str`
  * Produces: `Settings.AWS_LAMBDA_FUNCTION_NAME: str`
  * Produces: `Settings.AWS_LAMBDA_ENDPOINT_URL: Optional[str]`
- Acceptance criteria:
  * Given default configuration loadings, When FastAPI starts up, Then it reads environment variables matching AWS configs.
- Verification: Run `make build`
- Dependencies: None

### Task 2.2: Implement LambdaClient Service Class
- [x] Task Completed
- Scope: S
- Files:
  * `backend/app/services/lambda_client.py` (create)
- Interfaces:
  * Produces: `class SandboxTimeoutError(Exception)`
  * Produces: `class SandboxExecutionError(Exception)`
  * Produces: `class LambdaClient`
    * `__init__(self, settings: Settings)`
    * `async def execute_in_sandbox(self, code: str, test_suite: str, language: str) -> dict[str, Any]`
      * Returns: `{"stdout": str, "stderr": str, "passed": bool, "test_results": list[dict[str, Any]]}`
- Acceptance criteria:
  * Given sandbox payload inputs, When `execute_in_sandbox` is called, Then it invokes the AWS Lambda function synchronously (`InvocationType="RequestResponse"`), parses the output JSON, and returns it.
  * Given a function timeout error from AWS or Lambda client network failure, When calling the sandbox, Then raise `SandboxTimeoutError` or `SandboxExecutionError`.
- Verification: Local module import checks.
- Dependencies: Task 2.1

### Task 2.3: LambdaClient Unit & Integration Tests
- [x] Task Completed
- Scope: M
- Files:
  * `backend/tests/unit/test_lambda_client.py` (create)
- Interfaces:
  * Produces: `test_execute_in_sandbox_success(client: LambdaClient) -> None`
  * Produces: `test_execute_in_sandbox_timeout(client: LambdaClient) -> None`
  * Produces: `test_execute_in_sandbox_aws_error(client: LambdaClient) -> None`
  * Consumes: `execute_in_sandbox(self, code: str, test_suite: str, language: str) -> dict[str, Any]` from Task 2.2
- Acceptance criteria:
  * Given a mocked Boto3 client, When the FastAPI client makes calls, Then unit tests verify standard/error flows.
- Verification: `pytest backend/tests/unit/test_lambda_client.py`
- Dependencies: Task 2.2

### Checkpoint — Phase 2
- [ ] Backend client tests execute successfully and code coverage meets target criteria.
- Verification: Run `pytest backend/tests/unit/test_lambda_client.py`

---

## Phase 3: Infrastructure as Code (AWS CDK)

### Task 3.1: Initialize CDK App
- [ ] Task Completed
- Scope: S
- Files:
  * `infra/package.json` (create)
  * `infra/tsconfig.json` (create)
  * `infra/cdk.json` (create)
  * `infra/bin/infra.ts` (create)
- Interfaces:
  * None (CDK configuration scaffolding)
- Acceptance criteria:
  * Given TypeScript configuration files, When running `npm install`, Then TypeScript and AWS CDK libraries load cleanly.
- Verification: Run `cd infra && npm install`
- Dependencies: None

### Task 3.2: Create Isolated VPC and ECR Stack
- [ ] Task Completed
- Scope: S
- Files:
  * `infra/lib/sandbox-stack.ts` (create)
- Interfaces:
  * Produces: `class SandboxStack extends Stack`
- Acceptance criteria:
  * Given CDK VPC configuration, When synthesized, Then it defines a VPC containing isolated subnets with no internet gateway or NAT gateway routes.
  * Given ECR resource declarations, When synthesized, Then it provisions a private repository named `prompt-arena-sandbox`.
- Verification: Run `npx cdk synth` from the `infra/` folder.
- Dependencies: Task 3.1

### Task 3.3: Create Lambda Function & IAM Roles
- [ ] Task Completed
- Scope: S
- Files:
  * `infra/lib/sandbox-stack.ts` (modify)
- Interfaces:
  * None
- Acceptance criteria:
  * Given Lambda container settings, When synthesized, Then it defines a `DockerImageFunction` running inside the isolated VPC subnets with a 5-second execution timeout.
  * Given IAM execution profiles, When synthesized, Then it configures minimal execution policies restricting Lambda access to logging and network creation.
- Verification: Run `cd infra && npx cdk synth`
- Dependencies: Task 3.2

### Checkpoint — Phase 3
- [ ] AWS CDK stack compiles and synthesizes CloudFormation templates successfully.
- Verification: Run `cd infra && npx cdk synth`

---

## Plan Code Review
- [ ] Feature plan code review passed
