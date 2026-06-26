# Feature Requirements: Core Game Mechanics & Scoring

## Scope

In scope:
- Daily game limit enforcement at the backend API layer.
- 30-minute session duration management and automatic submission triggering.
- LLM proxy token budget tracking and enforcement.
- Single-file backend submission validation for Python and Node.js/TypeScript.
- Calculation of Correctness, Efficiency, and Speed sub-scores, and the combined Total Score.

Out of scope:
- Custom player-supplied Gemini API keys (all LLM usage must be proxy-managed).
- Multi-file workspace support.
- Runtimes other than Python and Node.js/TypeScript.
- Designing the public leaderboard and scorecard detailed frontend UIs.

## Decisions

Key technical decisions made:
- Daily limit increments must be done via Supabase Admin Client to bypass row-level security tampering checks.
- Sandbox execution uses the existing Docker sandbox orchestration model (`execute_code_locally`).

## Context

Why this feature is being built:
- To establish the core gameplay logic for Phase 3 of Prompt Arena, control LLM API costs through session token and daily play limitations, and calculate individual player scores accurately.

## Security Constraints [Conditional]

- **JWT Validation**: All game session API endpoints must validate user authorization headers via Supabase Auth API before taking any action.
- **Tampering prevention**: Daily play limits are incremented exclusively through the backend service role admin client, protecting profile states against client-side SQL/REST injections.

## Telemetry & Observability [Conditional]

- **Session Events**: Backend must log session state changes (`started`, `completed`, `failed`, `timed_out`) with associated session IDs and anonymized user details.
- **Proxy Token Usage**: The LLM proxy must log token usage metadata (input tokens, output tokens, total tokens) for audit trails and budget capping enforcement.
- **Sandbox Alerts**: Warnings must be logged when a sandbox container hits the 5-second timeout threshold.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to
- sdd-specs/features/2026-06-26-game-mechanics-scoring-spec.md — Core Game Mechanics & Scoring Feature Specification
- sdd-harness:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
