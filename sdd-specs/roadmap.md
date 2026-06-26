# Roadmap & Milestones

## Phase 1: Core Foundation & API Integration
**Duration**: 2 weeks
**Goal**: Establish the monorepo structure, database schemas, local sandbox emulator, and basic auth.

### Milestones
- [x] Establish root `Makefile` and setup environment configuration patterns
- [x] Design and apply the Supabase database schema (users, challenges, sessions, scorecards)
- [x] Build FastAPI server boilerplate with Supabase connectivity and Magic Link auth endpoints
- [x] Create a local Docker-based executor for test-running python/node snippets before integrating Lambda
- [x] Setup unit test frameworks (`pytest` and `vitest`) with basic test execution pipelines
- [x] Implement local containerized development and testing environment with Supabase emulation and Playwright E2E tests
- [x] Optimize local developer containers and align frontend with Magic Link / OTP auth flow
- [x] Backend Folder Structure Refactor [sdd-specs/features/2026-06-27-backend-folder-structure-refactor-spec.md](sdd-specs/features/2026-06-27-backend-folder-structure-refactor-spec.md)
  - [x] Refactor backend structure for simplified clean modules and update technical stack documentation


**Dependencies**: Supabase database setup

## Phase 2: Execution & LLM Backend
**Duration**: 1 week
**Goal**: Build the LLM token calculation proxy and deploy the live AWS Lambda runner.

### Milestones
- [ ] Gemini LLM Proxy [sdd-specs/features/2026-06-26-gemini-llm-proxy-spec.md](sdd-specs/features/2026-06-26-gemini-llm-proxy-spec.md)
  - [ ] Create the Python Gemini LLM proxy measuring and enforcing token budgets
- [ ] AWS Lambda Sandbox Runner [sdd-specs/features/2026-06-26-aws-lambda-sandbox-runner-spec.md](sdd-specs/features/2026-06-26-aws-lambda-sandbox-runner-spec.md)
  - [ ] Deploy the AWS Lambda Firecracker sandbox runner packaging Python/Node environments

**Dependencies**: AWS account setup (App Runner, Lambda), Google Gemini API credentials

## Phase 3: Game Workspace & Session Lifecycle
**Duration**: 1 week
**Goal**: Build the player workspace interface and session lifecycle orchestration.

### Milestones
- [ ] Game Session & Arena Workspace [sdd-specs/features/2026-06-26-game-session-workspace-spec.md](sdd-specs/features/2026-06-26-game-session-workspace-spec.md)
  - [ ] Build React frontend with side-by-side Monaco editor layout
  - [ ] Implement the simulated console/terminal component in the webapp
  - [ ] Implement frontend-backend websocket/polling mechanism for test runner execution
  - [ ] Build game timer logic (30-minute hard cap) and server-backed session boundaries

**Dependencies**: Phase 2 completion

## Phase 4: Game Mechanics & Public Spectating
**Duration**: 1 week
**Goal**: Finalize scoring calculations, daily game limitations, leaderboards, and deploy to production.

### Milestones
- [ ] Core Game Mechanics & Scoring [sdd-specs/features/2026-06-26-game-mechanics-scoring-spec.md](sdd-specs/features/2026-06-26-game-mechanics-scoring-spec.md)
  - [ ] Write scoring calculation logic (Correctness + Efficiency + Speed)
  - [ ] Enforce the exactly-1-game-per-day restriction at the backend service layer
- [ ] Public Spectator Dashboard [sdd-specs/features/2026-06-26-public-spectator-dashboard-spec.md](sdd-specs/features/2026-06-26-public-spectator-dashboard-spec.md)
  - [ ] Create the public spectator dashboard displaying the live leaderboard
  - [ ] Build the detailed scorecard detail viewer displaying code submissions and metrics
- [ ] Deploy the frontend to AWS Amplify and the backend to AWS App Runner


## Rollout Plan

How/when to deploy:
- **Development**: Local development environments with docker-compose database and local LLM mock.
- **Staging**: Deploy frontend (Amplify) and backend (App Runner) connected to Supabase development database and AWS Lambda sandbox.
- **Production**: Public release with invited software engineer emails whitelisted for signup.
