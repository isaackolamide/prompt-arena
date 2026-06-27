# ADR-001: Local Supabase Simulation Strategy

## Status
Accepted

## Date
2026-06-25

## Context
We need a local database and auth simulation stack for development and testing. Key requirements:
- Emulate the Supabase stack locally (PostgreSQL database, Auth GoTrue API, REST PostgREST API gateway).
- Support automated execution of database migrations and seeds.
- Allow containerized app services (React frontend, FastAPI backend) to run inside Docker Compose while communicating with the simulated Supabase services.

## Decision
Use the official Supabase CLI emulator (`npx supabase`) on the host machine to manage the database, auth, and gateway services, and a root-level `docker-compose.yml` configuration for the application services (`frontend` and `backend`), configured to communicate with the host via `host.docker.internal`.

## Alternatives Considered

### Direct Docker Compose Integration (Bypassing Supabase CLI)
- Pros: Everything is controlled via a single `docker-compose.yml` file, independent of any host CLI tools.
- Cons: We would need to manually configure Kong API gateway routes, GoTrue configuration files, and PostgreSQL settings, which is highly complex and prone to drifts from the production environment. We would also lose the Supabase Studio dashboard and Inbucket (local email client) out-of-the-box.
- Rejected: Maintaining custom compose configurations for complex third-party stacks increases operational overhead.

### Full Host Execution (No Containers)
- Pros: Simpler local networking.
- Cons: Developers must manage global software dependencies, and local dev environments can easily become dirty and out-of-sync.
- Rejected: Does not satisfy containerized isolation requirement.

## Consequences
- Developers must have Docker and Supabase CLI dependencies installed on the host.
- The root `Makefile` will orchestrate the startup of the Supabase CLI emulator alongside the `docker-compose` services.
- Local database configurations in `.env` will target `http://host.docker.internal:54321` inside compose and `http://localhost:54321` on the host.
