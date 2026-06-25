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


**Dependencies**: Supabase database setup

## Phase 2: LLM Proxy, Sandbox & Workspace
**Duration**: 2 weeks
**Goal**: Build the player workspace interface, LLM token calculation proxy, and live AWS Lambda runner.

### Milestones
- [ ] Build React frontend with side-by-side Monaco editor layout
- [ ] Implement the simulated console/terminal component in the webapp
- [ ] Create the Python Gemini LLM proxy measuring and enforcing token budgets
- [ ] Deploy the AWS Lambda Firecracker sandbox runner packaging Python/Node environments
- [ ] Implement frontend-backend websocket/polling mechanism for test runner execution
- [ ] Build game timer logic (30-minute hard cap) and server-backed session boundaries

**Dependencies**: AWS account setup (App Runner, Lambda), Google Gemini API credentials

## Phase 3: Game Mechanics & Public Spectating
**Duration**: 1 week
**Goal**: Finalize scoring calculations, daily game limitations, leaderboards, and deploy to production.

### Milestones
- [ ] Write scoring calculation logic (Correctness + Efficiency + Speed)
- [ ] Enforce the exactly-1-game-per-day restriction at the backend service layer
- [ ] Create the public spectator dashboard displaying the live leaderboard
- [ ] Build the detailed scorecard detail viewer displaying code submissions and metrics
- [ ] Deploy the frontend to AWS Amplify and the backend to AWS App Runner

## Rollout Plan

How/when to deploy:
- **Development**: Local development environments with docker-compose database and local LLM mock.
- **Staging**: Deploy frontend (Amplify) and backend (App Runner) connected to Supabase development database and AWS Lambda sandbox.
- **Production**: Public release with invited software engineer emails whitelisted for signup.
