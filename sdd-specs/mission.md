# Project Mission

## Objective

What are we building?
- A web-based coding game with a side-by-side Monaco editor and simulated terminal, evaluating players on code correctness, token budget efficiency, and completion speed.

Why?
- To evaluate spec-driven development, context window optimization, and prompt engineering in a fun, competitive, and zero-install environment.

Who is the user?
- Invited and authenticated software engineers (players) and public spectators.

What does success look like?
- Players can play exactly one game per day to control API cost.
- Code runtimes are sandboxed and executed securely on AWS Lambda.
- User session data and scorecards are tracked in Supabase.
- Spectators can view a live public leaderboard and individual scorecard details.

## Boundaries

### Always Do
- Enforce authentication checks (Supabase Auth magic links/OTP) for all player game actions.
- Proxy and intercept Gemini API prompts to calculate input/output token usage strictly.
- Follow Test-Driven Development (TDD) for all logical changes.
- Use mock builders or factories to set up test objects/state to keep tests isolated.
- Keep the AWS Lambda execution timeout capped at 5 seconds and disable network access.

### Ask First
- Changes to the scoring formula weight (Correctness, Efficiency, Speed).
- Adding additional runtimes beyond Python and Node.js/TypeScript.
- Increasing Supabase usage beyond the free tier limits.

### Never Do
- Allow visual layout or DOM manipulation coding challenges (backend only).
- Support multi-file project workspaces for players (single-file submissions only).
- Allow custom player-supplied Gemini API keys (all LLM usage must be proxy-managed).
- Execute user submissions directly on the backend container (must use AWS Lambda sandbox).

## Quick Commands

```bash
Build: make build
Test: make test
Lint: make lint
Dev: make dev
```
