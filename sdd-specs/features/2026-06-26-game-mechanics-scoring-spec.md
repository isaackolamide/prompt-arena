# Feature Spec: Core Game Mechanics & Scoring

## Objective
Establish the core game rules, constraints, and scoring calculations for the Prompt Arena. This ensures fair, cost-controlled, and timed competition among invited players.

## User & Stakeholder
Invited and authenticated software engineers (players) who compete, and system administrators who require API cost controls and backend security.

## Acceptance Criteria
- Given a player attempts to start a game, when they have already completed a game today, then they are blocked at the backend service layer and shown a daily limit error.
- Given a player starts a game, when the session is initialized, then a strict 30-minute timer starts, and the game automatically submits the current workspace when the timer hits zero.
- Given a player submits a solution, when the workspace is evaluated, then the code is checked to ensure it is a single file targeting a supported backend runtime (Python or Node.js/TypeScript).
- Given a player makes LLM queries via the workspace, when the prompt or response occurs, then the proxy tracks and subtracts tokens from their challenge-specific budget, blocking further prompts if the budget is exceeded.
- Given a player completes a challenge, when their scorecard is created, then the total score is computed using the formula:
  $$\text{Total Score} = \frac{\text{Correctness} + \text{Efficiency} + \text{Speed}}{3}$$
  - **Correctness**: $\frac{\text{Passed Unit Tests}}{\text{Total Unit Tests}} \times 100$
  - **Efficiency**: $\frac{\text{Token Budget} - \text{Tokens Used}}{\text{Token Budget}} \times 100$ (capped at 0 if budget exceeded)
  - **Speed**: $\frac{\text{Remaining Time (seconds)}}{\text{Total Time (1800 seconds)}} \times 100$

## Technical Constraints
(derived from sdd-specs/mission.md boundaries and sdd-specs/tech-stack.md)
- All player game actions must strictly enforce Supabase OTP/Magic Link authentication checks.
- Gemini API prompts must go through the proxy to measure and enforce the token budget.
- Submissions must be executed securely within the AWS Lambda sandbox, with a strict 5-second timeout and no network access.
- Code workspace must support single-file submissions only (no multi-file projects).
- No frontend visual layout or DOM manipulation challenge types are permitted (backend only).
- All logical scoring changes must follow Test-Driven Development (TDD) with tests implemented in `backend/tests/` and using mock builders to isolate state.

## In Scope
- Daily game limit enforcement at the backend service layer.
- 30-minute session duration management and automatic submission triggering.
- LLM proxy token budget tracking and enforcement.
- Single-file backend submission validation for Python and Node.js/TypeScript.
- Calculation of Correctness, Efficiency, and Speed sub-scores, and the combined Total Score.

## Out of Scope
- Custom player-supplied Gemini API keys (all LLM usage must be proxy-managed).
- Multi-file workspace support.
- Runtimes other than Python and Node.js/TypeScript.
- Designing the public leaderboard and scorecard detailed frontend UIs (handled in separate visual stories).

## Dependencies
- Supabase database schema for users, challenges, sessions, and scorecards (sdd-specs/roadmap.md Phase 1).
- LLM proxy token tracking capabilities and AWS Lambda sandbox runner (sdd-specs/roadmap.md Phase 2).

## Stakeholder Flags
(mission.md "Ask First" items this feature touches — require explicit approval before implementation)
- **Scoring formula weights**: The equal weighting (1/3 each for Correctness, Efficiency, and Speed) is configured as the default; changes to these weights require explicit stakeholder approval.

## Success Metrics
- Players are prevented from running more than one game per calendar day.
- Player solutions that run longer than 5 seconds or attempt network requests are terminated securely by the sandbox.
- The scoring calculations correctly reflect test outputs, token consumption from proxy logs, and exact session timing metrics.
