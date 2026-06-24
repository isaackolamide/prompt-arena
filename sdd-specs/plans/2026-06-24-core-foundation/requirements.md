# Feature Requirements: core-foundation

## Scope

In scope:
- Root repository layout initialization with `Makefile` targets.
- Local testing pipeline configuration using `pytest` (backend) and `vitest` (frontend).
- Supabase SQL schema design and application structure mapping profiles, challenges, sessions, and scorecards.
- FastAPI server boilerplate with Supabase client integrations.
- User authentication via passwordless Magic Link and OTP verification endpoints.
- Containerized sandbox runtime (Docker-based) for running Python and Node.js code locally.
- Execution boundaries: 5-second hard execution timeout and network disabled inside the sandbox container.
- Workspace-level `.agents/AGENTS.md` rules file.

Out of scope:
- Live AWS Lambda packaging or AWS deployment (Lambda, App Runner, Amplify).
- Gemini API proxying, token counting, or prompt interceptors.
- Game timer websocket handlers or daily game cap API-level logic.
- Monaco Editor web interface, simulated terminal UI component, and spectator leaderboard dashboard.
- Custom score calculations or advanced statistics reporting.

## Decisions

Key technical decisions made:
- **Local Sandbox Alternative**: Use a local Docker container (using the Docker SDK for Python) to execute code snippets rather than deploying AWS Lambda during Phase 1. This matches Lambda's microVM security characteristics (timeout, network block) for local dev/testing.
- **FastAPI / Supabase SDK**: Integrate the official `supabase-py` client library to interact with Supabase DB and Supabase Auth.
- **Mocked DB/Auth for Tests**: Mock external API calls to Supabase in backend tests to prevent external dependency on live Supabase during local test execution.

## Context

Why this feature is being built:
- To establish the baseline codebase infrastructure, auth flow, schema, and local execution mechanism needed before constructing the user interface and Gemini proxy integration.

## Security Constraints [Security Sensitive]
- **API Secret Keys**: Supabase credentials and Gemini keys must never be hardcoded. They must be loaded via environment variables and configured in a git-ignored `.env` file.
- **Magic Link Validation**: OTP tokens and Magic Links must be validated strictly through the Supabase Authentication service.
- **Sandbox Execution Isolation**: Code executed in the local sandbox container must not have access to the host network, host filesystem, or standard Docker host integrations. Hard-limit container timeout to 5 seconds.

## Telemetry & Observability [Telemetry Required]
- **Boilerplate Logging**: FastAPI app must configure standard Python structured logging (`logging.getLogger("app")`).
- **Sandbox Execution Telemetry**: The executor service must log stdout, stderr, execution duration, and container exit codes for every snippet run.

## Migration & Deprecation Plan [Migration Risk]
- **Database Bootstrapping**: Since this is the initial database setup, schema changes are applied via a bootstrapping SQL script. Subsequent database schema modifications in Phase 2/3 must be handled using structured database migrations.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to
- harnesspowers:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
- harnesspowers:references/clean-architecture-ddd-reference.md — Clean Architecture and DDD structural/layer rules (mapped conceptually to Python and TypeScript)
