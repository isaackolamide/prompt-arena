# Developer Agent Guide - Prompt Arena

This document defines the strict constraints, commands, styling guidelines, and engineering principles for all developer agents working on the Prompt Arena codebase.

## Behaviour

- Surface assumptions before building — wrong assumptions held silently are the most common failure mode
- Stop and ask when requirements conflict — don't guess
- Push back when warranted — not a yes-machine
- Prefer the boring, obvious solution — cleverness is expensive
- Touch only what you're asked to touch — don't refactor adjacent systems

## Tech Stack & Code Style

### Python (Backend)
- Files: `snake_case.py` for all source files, `test_*.py` for test files
- Functions/Variables/Modules: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Indentation: 4 spaces
- Line length: 88 characters max (Ruff default)
- Safety: Strict Pydantic models for request/response payloads, fully type-hinted function signatures.

### TypeScript (Frontend)
- Files: `PascalCase.tsx` React components, `camelCase.ts` helper scripts, `name.test.tsx` or `name.test.ts` for tests
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Classes/Types/Interfaces: `PascalCase`
- Indentation: 2 spaces
- Line length: 100 characters max
- Safety: No `any` type escapes. Ensure strict type safety.

## Key CLI Commands

Run these standard commands from the repository root:

- `make build` - Prepares project skeleton, initializes `.env`, and installs dependencies.
- `make test` - Runs both pytest (backend) and vitest (frontend) suites.
- `make lint` - Runs linting and static analysis (ruff / eslint).
- `make clean` - Cleans build artifacts and caches.
