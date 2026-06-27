# Prompt Arena

Prompt Arena is a web-based coding game designed to evaluate developers on spec-driven development, context window optimization, and prompt engineering. The platform features a side-by-side Monaco editor and simulated terminal, scoring players on code correctness, token budget efficiency, and completion speed.

## Architecture & Dev Environment

The local development environment uses:
- **FastAPI (Python)** for the backend API, routing, and sandbox executions.
- **Vite + React (TypeScript)** for the frontend developer workspace and Monaco editor.
- **Supabase CLI** on the host machine to run PostgreSQL database, Auth GoTrue API, and API Gateway services.
- **Docker Compose** to coordinate local containerized frontend and backend services.
- **AWS Lambda Sandbox Emulator (Docker)** to execute player code submissions in an isolated environment with zero network or database access.

---

## Directory Structure

- [backend/](./backend) — FastAPI application source code and pytest suite.
- [frontend/](./frontend) — Vite + React + TypeScript workspace, including Monaco editor components and Vitest/Playwright tests.
- [sandbox-lambda/](./sandbox-lambda) — AWS Lambda runner packaging python/node sandboxes.
- [supabase/](./supabase) — Local Supabase configurations, database migrations, and schema seeds.
- [sdd-specs/](./sdd-specs) — Project specifications, features, implementation plans, and roadmap details.
- [sdd-docs/](./sdd-docs) — Architectural Decision Records (ADRs) and decision notes.
- [sdd-notes/](./sdd-notes) — Developer logs and local notes.

---

## Prerequisites

Ensure the following tools are installed on your host machine:
- **Docker & Docker Compose** (Desktop running)
- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)

---

## Getting Started

1. **Setup dependencies and environment configuration:**
   Initialize your local [.env](.env) file from the template and install Python/Node dependencies by running:
   ```bash
   make setup
   ```

2. **Build container environments:**
   Build the sandbox container image and project directories:
   ```bash
   make build
   ```

3. **Start the local stack:**
   Boot the local Supabase CLI emulator, sync local credentials to [.env](.env), and spin up the frontend and backend Docker containers:
   ```bash
   make start
   ```
   - **Frontend**: http://localhost:5173
   - **Backend**: http://localhost:8000
   - **Supabase Console**: http://localhost:54323

4. **Stop the local stack:**
   Shut down the Docker containers and stop the local Supabase emulator:
   ```bash
   make stop
   ```

---

## Key CLI Commands

All development tasks are managed via targets in the [Makefile](./Makefile):

| Command | Description |
| :--- | :--- |
| `make setup` | Copy [.env.example](./.env.example) to [.env](.env) and install python/npm modules. |
| `make build` | Set up workspace directories and build the local sandbox-lambda Docker image. |
| `make start` | Boot Supabase emulator, sync credentials, and start frontend/backend docker services. |
| `make stop` | Stop all active local Docker services and the Supabase emulator. |
| `make test` | Run both the python pytest backend suite and vitest frontend suite. |
| `make test-unit` | Run only the backend and frontend unit tests. |
| `make test-integration` | Spin up a temporary postgres container, run migrations, and execute database integration tests. |
| `make test-e2e` | Run Playwright end-to-end tests targeting the active frontend compose service. |
| `make lint` | Run ruff (backend) and eslint/tsc (frontend) static analyzers. |
| `make clean` | Clean build caches, temporary test artifacts, and python/node caches. |

---

## Code & Testing Conventions

Please refer to the following specification files for style guidelines and development patterns:
- See [mission.md](./sdd-specs/mission.md) for core project boundaries and objectives.
- See [tech-stack.md](./sdd-specs/tech-stack.md) for naming conventions and type-safety rules.
- Follow Test-Driven Development (TDD) for all logical changes.