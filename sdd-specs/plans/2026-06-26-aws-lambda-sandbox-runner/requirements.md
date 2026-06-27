# Feature Requirements: 2026-06-26-aws-lambda-sandbox-runner

## Scope

In scope:
- Python execution handler wrapper `lambda_handler` in `sandbox-lambda/runner.py`.
- Docker build configurations in `sandbox-lambda/Dockerfile` tailored for AWS Lambda runtime container image support (installing `awslambdaric` interface client).
- FastAPI backend client service `LambdaClient` in `backend/app/services/lambda_client.py` using `boto3` to synchronously invoke the remote Lambda sandbox.
- Backend configuration updates in `backend/app/core/config.py` loading AWS region, endpoints, and credentials safely.
- Infrastructure definition scripts in `infra/` folder utilizing TypeScript AWS CDK to automate VPC setup, ECR hosting, Lambda container provisioning, and IAM least-privilege configurations.
- Unit and integration tests covering the Lambda handler execution and `LambdaClient` invocation.

Out of scope:
- Frontend Monaco Editor React layout components and layout adjustments.
- WebSocket or long polling mechanism orchestration on the client/frontend.
- Supabase session management/database schema updates (already completed in Phase 1 database setup).
- Gemini API model interaction and token calculation proxy (managed separately by the LLM proxy).

## Decisions

Key technical decisions made:
- **Lambda Container Packaging:** Adopt container-based Lambda deployment rather than zip packages, enabling bundling of complete Python 3.x and Node.js runtime environments (including testing frameworks like pytest/vitest dependencies) without exceeding AWS zip size constraints.
- **Outbound Network Filtering:** Deploy the Lambda function strictly within a VPC containing isolated subnets (no Internet Gateways, no NAT Gateways, no routes to the public internet). This physical separation guarantees that players cannot execute code making outbound HTTP/socket calls to steal secrets or query external endpoints.
- **AWS CDK IaC:** Utilize TypeScript-based AWS CDK to maintain infrastructure definitions. This matches the team's language strengths (TypeScript frontend) and enables cleaner container-to-lambda build integration (`DockerImageFunction`) compared to verbose Terraform JSON/HCL configurations.
- **Fallback Dev Emulator Support:** The `LambdaClient` will recognize an optional `AWS_LAMBDA_ENDPOINT_URL` configuration. If configured, it redirects Boto3 calls to a local LocalStack container or alternative local emulation client rather than public AWS endpoints, easing offline testing.

## Context

Why this feature is being built:
- Players submit raw code to be tested. Running untrusted code directly on the API server container poses severe host compromise risks (e.g. system commands, data manipulation, memory access).
- Distributing execution to ephemeral, isolated Firecracker microVMs ensures absolute backend safety and resource-cap enforcement (timeouts, network, disk limits).

## Security Constraints

- **Minimal IAM Execution Role:** The Lambda sandbox execution role must only have permissions to output CloudWatch logs and attach network interfaces to the VPC isolated subnets. It must possess no access to other AWS services (e.g., S3, DynamoDB, Supabase).
- **Backend Invocation Restriction:** The FastAPI server execution credentials (IAM User/Role) must only be granted `lambda:InvokeFunction` permissions restricted to the sandbox ARN.
- **Execution Time Limits:** Set the Lambda function execution timeout strictly to 5 seconds to force termination of CPU-exhaustion scripts (e.g. infinite loops).
- **VPC Subnet Isolation:** Subnets allocated to the sandbox execution must possess zero routing to an internet gateway, virtual private gateway, or NAT instance.

## Telemetry & Observability

- **Structured Sandbox Logs:** Emit standardized JSON log messages from `LambdaClient` during runtime execution:
  * `sandbox_run_started`: Emitted upon sandbox invocation request containing challenge metadata and runtime language details.
  * `sandbox_run_completed`: Emitted on successful test execution return containing passed/failed counts, runtime duration, and exit status.
  * `sandbox_run_failed`: Emitted on sandbox timeout or execution error containing details on the failure trace.
- **Upstream Latency Monitoring:** Measure execution duration for sandbox invocations to track system responsiveness (target < 2 seconds round-trip excluding cold starts).
- **Error Tracking:** Alert administrators if Lambda container invocation failure rate (e.g., AWS service availability exceptions, Docker package initialization errors) exceeds 1% over a 15-minute window.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to (Phase 2)
- sdd-specs/features/2026-06-26-aws-lambda-sandbox-runner-spec.md — Feature Spec: AWS Lambda Sandbox Runner
- sdd-harness:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
- sdd-harness:references/clean-architecture-ddd-reference.md — Clean Architecture and DDD structural/layer rules. (Note: For Python/FastAPI, map concepts conceptually: presentation layer in `api/`, service layer in `services/`, database layer in `db/`).
