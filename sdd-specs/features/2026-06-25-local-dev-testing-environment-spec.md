# Feature Spec: Local Containerized Dev & Testing Environment

## Objective
Establish a unified local development and testing environment with containerized React frontend, FastAPI backend, local Supabase CLI simulation, and automated testing (unit, integration, and Playwright E2E) to facilitate safe, isolated, and rapid development.

## User & Stakeholder
Software engineers (developers/contributors) working on the Prompt Arena project.

## Acceptance Criteria
- [ ] Given a new developer checkout, When `make setup` is run, Then host-level dependencies (npm, pip), `.env` templates, and Playwright browsers are installed and configured.
- [ ] Given a configured host, When `make start` is run, Then the React frontend, FastAPI backend, and Supabase CLI emulator services build and run in Docker compose, and database migrations/seeds are executed automatically.
- [ ] Given a running local environment, When `make test-unit` is run, Then unit tests run for backend via `pytest` (using mocked database handlers) and frontend via `vitest` (in `jsdom` mode) and exit cleanly.
- [ ] Given a local setup, When `make test-integration` is run, Then a temporary containerized PostgreSQL/Supabase test database is booted, migrations are run, backend integration tests execute, and the container is torn down.
- [ ] Given a running local environment, When `make test-e2e` is run, Then Playwright runs end-to-end tests targeting the containerized frontend URL.
- [ ] Given a running local sandbox execution container, When executing user-submitted code snippets, Then the executor has no network or database access and cannot access the host.

## Technical Constraints
(derived from sdd-specs/mission.md boundaries and sdd-specs/tech-stack.md)
- **Sandbox Isolation**: The local sandbox executor container running user-submitted code must be strictly isolated from internal Docker Compose networking bridges (no access to DB, Backend API, or host services).
- **Secrets Management**: Credentials, JWT secrets, and keys must remain in a git-ignored `.env` file, loaded at runtime via environment variables inside the Docker Compose service contexts.
- **Database Cleanliness**: Integration and E2E databases must run in separate isolated schemas/databases from development to avoid state contamination.

## In Scope
- Unified local tooling setup via root `Makefile` targets.
- Containerized fullstack app (React frontend, FastAPI backend) using `docker-compose`.
- Supabase DB simulation (PostgreSQL, Auth GoTrue API, REST API gateway) locally inside Docker using the official Supabase CLI emulator.
- Automated bootstrapping of PostgreSQL schema and database seeds.
- Playwright E2E testing framework integration targeting the containerized frontend.
- Isolated sandbox execution container setup.

## Out of Scope
- Cloud deployment scripts (AWS Amplify, AWS App Runner).
- Production-grade SSL configuration for local development.

## Dependencies
- Docker & Docker Compose installed on the developer's host machine.
- Supabase CLI installed on the developer's host machine.
- Existing codebase structure outlined in `sdd-specs/tech-stack.md`.
- Boundaries specified in `sdd-specs/mission.md`.

## Stakeholder Flags
- none

## Success Metrics
- Bootstrap time for a new developer environment is reduced to a single command (`make setup`).
- 100% of integration and E2E tests run successfully in local isolation without polluting the development database.
- Developers can build, run, and test the entire project locally without requiring external cloud accounts or paid resources.
