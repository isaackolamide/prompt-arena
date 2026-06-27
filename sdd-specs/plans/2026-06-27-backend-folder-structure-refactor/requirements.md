# Feature Requirements: Backend Folder Structure Refactor

## Scope

In scope:
- Creating the new `backend/app/schemas/` folder.
- Extracting existing Pydantic request/response validation schemas from `backend/app/api/auth.py` and migrating them to `backend/app/schemas/auth.py`.
- Correcting python absolute/relative imports in all `backend/app/` source modules.
- Re-aligning backend test files under `backend/tests/` to import application components correctly (including standardizing imports in `backend/tests/test_executor.py`).
- Verifying the entire backend application compiles, runs, tests, and lints successfully.

Out of scope:
- Restructuring frontend components or frontend styles.
- Database schemas, schema migrations, or data alterations.
- Altering core routing URL paths or changing API endpoint payload structures (backward-compatible API contract is strictly preserved).
- Refactoring adjacent systems or libraries.

## Decisions

Key technical decisions made:
- **FastAPI Standard Alignment**: Adopted standard FastAPI layers (`api/`, `core/`, `db/`, `schemas/`, `services/`) to maximize development velocity and minimize imports/abstraction boilerplate.
- **DTO Separation**: Extracted schemas from route definitions to make request/response validation objects highly modular and reusable for future backend routers.
- **Unified Import Patterns**: Standardized import style across all test files to use the local `app.` path instead of varying absolute pathways like `backend.app.`.

## Context

Why this feature is being built:
- The previous configuration specified a Clean Architecture/DDD setup with 15+ subdirectories. This pattern introduces substantial boilerplate code and unnecessary layers of abstraction for a simple daily-coding game backend, slowing down onboarding and feature implementation. Restructuring now establishes a pragmatic codebase.

## Migration & Deprecation Plan

- **In-place Refactor**: Restructure imports within existing backend modules without introducing deprecation windows, as this is a purely internal codebase migration.
- **Route Preservation**: Ensure no HTTP route names or decorators in `backend/app/api/auth.py` are modified to prevent any breaking changes to client/frontend consumers.
- **Dead Imports Removal**: Remove local validation class imports from `backend/app/api/auth.py` and replace them with import statements referencing `app.schemas.auth`.

## References
- sdd-specs/mission.md — Project objective and boundaries
- sdd-specs/tech-stack.md — Technical constraints and code style
- sdd-specs/roadmap.md — Phase this feature belongs to
- sdd-specs/features/2026-06-27-backend-folder-structure-refactor-spec.md — Backend Folder Structure Refactor Feature Spec
- sdd-harness:references/testing-patterns.md — Testing patterns reference for TDD, assertions, and mocking boundaries
