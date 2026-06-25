# Feature Requirements: 2026-06-25-local-dev-testing-environment

## Scope

In scope:
- Unified local tooling setup via root `Makefile` targets (`make setup`, `make start`, `make stop`, `make test-unit`, `make test-integration`, `make test-e2e`).
- Containerized frontend (React Vite) and backend (FastAPI) applications running under `docker-compose`.
- Supabase DB simulation (PostgreSQL, Auth GoTrue API, REST API gateway) locally inside Docker using the official Supabase CLI emulator.
- Automated bootstrapping of PostgreSQL schema and database seeds during startup.
- Playwright E2E testing framework integration targeting the containerized frontend.
- Programmatic PostgreSQL test database container creation, schema execution, and destruction for backend integration tests.
- Isolated sandbox execution container setup verifying no network or database access for user code.

Out of scope:
- Cloud deployment scripts (AWS Amplify, AWS App Runner).
- Production-grade SSL configuration for local development.

## Decisions

Key technical decisions made:
- **ADR-001: Local Supabase Simulation Strategy**: Use the official Supabase CLI emulator on the host machine, and run React frontend and FastAPI backend inside a custom root `docker-compose.yml` communicating with the host Supabase services via `host.docker.internal`.
- **Programmatic Integration Test Database**: Use the Python `docker` SDK to dynamically spin up a clean `postgres:15-alpine` container during pytest integration runs, execute migrations, and clean it up automatically upon completion. This keeps test runs entirely isolated and independent of the active development database state.

## Context

Why this feature is being built:
- To establish a unified local development and testing environment that enables isolated, rapid development cycles and ensures code correctness before deployment, without requiring external cloud accounts or paid resources.

## Security Constraints

*(Security Sensitive feature classification)*
- **Secrets Management**: Credentials, JWT secrets, and keys must remain in a git-ignored `.env` file, loaded at runtime via environment variables inside the Docker Compose service contexts.
- **CORS Scope**: FastAPI CORS middleware must restrict allowed origins to known local client URLs (`http://localhost:3000`, `http://localhost:5173`) and avoid wildcard `*` exposures.
- **Sandbox Isolation**: The sandbox execution container running user-submitted code snippets must use `network_mode="none"`, memory limits, CPU quotas, and run as a non-root `sandbox` user to prevent host or database penetration.

## Telemetry & Observability

*(Telemetry Required feature classification)*
- **Startup Diagnostics**: The `make start` target must log clear status updates. If Supabase CLI fails to start, migrations fail to apply, or containers fail to build, a distinct error traceback must be output.
- **Health Checks**: The backend container must expose a `/health` endpoint returning `{"status": "ok"}` which is polled by the setup/compose stack to verify readiness.
- **Database Logs**: PostgreSQL container stdout/stderr logs must be accessible to let developers debug query errors locally.

## Migration & Deprecation Plan

*(Migration Risk feature classification)*
- **Schema Migrations**: The existing `backend/app/db/schema.sql` is migrated to the initial Supabase migration structure under `supabase/migrations/20260625000000_init_schema.sql` to serve as the database schema base.
- **Schema Evolution**: Moving forward, developers must generate new migration files inside `supabase/migrations/` rather than modifying `schema.sql` directly. The `make start` process applies all pending migrations in chronological order automatically.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to
- sdd-specs/features/2026-06-25-local-dev-testing-environment-spec.md — Local Containerized Dev & Testing Environment
- sdd-docs/decisions/ADR-001-local-supabase-simulation-strategy.md — Local Supabase Simulation Strategy
- harnesspowers:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
