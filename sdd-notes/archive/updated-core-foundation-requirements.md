# Feature Requirements: Local Containerized Dev & Testing Environment

## Scope

In scope:
- **Unified Local Tooling Setup**: A single command to prepare the developer workspace (check environments, copy templates, pull/install dependencies).
- **Containerized Fullstack App**: Run React frontend, FastAPI backend, and a simulated database stack in local containers using `docker-compose`.
- **Supabase DB Simulation**: Emulate the Supabase backend (PostgreSQL database, Auth GoTrue API, REST API gateway) locally inside Docker using the official Supabase CLI emulator.
- **Automated DB Seed & Migration**: Automated bootstrapping of the PostgreSQL schema and seeds for local testing.
- **One-Command Testing Pipeline**:
  - **Unit Testing**: Run fast, mocked tests locally for both backend (`pytest`) and frontend (`vitest`).
  - **Integration Testing**: Run backend API tests against a real, temporary containerized PostgreSQL/Supabase database.
  - **E2E Testing**: Run Playwright tests against the containerized frontend, verifying key user flows.

Out of scope:
- Cloud deployment scripts (AWS Amplify, AWS App Runner).
- Production-grade SSL configuration for local development.

---

## Technical Decisions

- **Container Orchestration**: Use `docker-compose.yml` to coordinate the network, storage, and life-cycle of the frontend, backend, and Supabase local stack.
- **Database Simulation**: Avoid third-party cloud mocks (like LocalStack). Use the official **Supabase CLI** local development framework (which spawns standard Docker containers for PostgreSQL, Kong, GoTrue, and PostgREST).
- **E2E Testing Engine**: Use **Playwright** running inside or outside the container network, targeting the containerized frontend URL.
- **Unified Command Interface**: Expose all actions through the root `Makefile` targets.

---

## Commands Specification

A developer should be able to run these exact targets from the project root:

1. **`make setup`**:
   - Initializes `.env` from templates.
   - Installs host-level developer dependencies (`npm install` for frontend, `pip install` for backend).
   - Installs Playwright test browsers.
2. **`make start`**:
   - Starts all fullstack services (Frontend, Backend, Supabase Emulator) via `docker compose up --build -d`.
   - Runs database migrations/seeds.
3. **`make test-unit`**:
   - Runs lightweight unit tests: `pytest` with mocked database handlers and `vitest` in `jsdom` mode.
4. **`make test-integration`**:
   - Boots a temporary PostgreSQL/Supabase test database container.
   - Runs migrations.
   - Runs the backend integration tests (`pytest`) against it, then tears down the container.
5. **`make test-e2e`**:
   - Ensures the full stack is running.
   - Executes the Playwright E2E suite against the running frontend container.

---

## Security Constraints [Security Sensitive]

- **Host vs. Sandbox Network Isolation**: The local sandbox executor container (running user-submitted code) must be strictly isolated from the internal Docker Compose networking bridges (no access to DB, Backend API, or host services).
- **Secrets Management**: Credentials, JWT secrets, and keys must remain in a git-ignored `.env` file, loaded at runtime via environment variables inside the Docker Compose service contexts.
- **Test Database Cleanliness**: Integration and E2E databases must run in separate isolated schemas/databases from development to avoid state contamination.

---

## Telemetry & Observability [Telemetry Required]

- **Build Logging**: Detailed logs of container build steps, database seeds, and test runner outputs should be piped directly to stdout during execution.
- **Clean Teardown Logging**: Containers must log clear state shutdowns to ensure no dangling Docker volumes or networks occupy memory/ports.
