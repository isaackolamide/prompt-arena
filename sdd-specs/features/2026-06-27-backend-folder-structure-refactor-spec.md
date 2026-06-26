# Feature Spec: Backend Folder Structure Refactor

## Objective
Refactor the backend application directory structure from a highly-nested, over-engineered Clean Architecture/DDD pattern to a simplified, layer-based FastAPI layout. This reduces imports/dependency boilerplate, enhances maintainability, and aligns with the project's core KISS/YAGNI principles.

## User & Stakeholder
Software developers and contributors maintaining the Prompt Arena backend.

## Acceptance Criteria
- [ ] Restructure `backend/app/` to have only the following layout:
  - `backend/app/api/` for endpoint route handlers and common endpoint dependencies (`dependencies.py`).
  - `backend/app/core/` for app configurations, constants, and settings (`config.py`).
  - `backend/app/db/` for database helper clients, connections, and initial schemas.
  - `backend/app/schemas/` for Pydantic models handling request/response validation (DTOs).
  - `backend/app/services/` for business logic (e.g., executors, proxies, calculators).
- [ ] Move existing files to their appropriate directories:
  - Move/Verify `backend/app/core/config.py` is in `backend/app/core/`.
  - Move/Verify `backend/app/db/supabase.py` (and any DB schemas/configs) is in `backend/app/db/`.
  - Move/Verify `backend/app/services/executor.py` is in `backend/app/services/`.
  - Move/Verify `backend/app/api/auth.py` is in `backend/app/api/`.
  - Maintain `backend/app/main.py` at the root of `backend/app/`.
- [ ] Update all python import paths (both absolute `app.services.executor`, etc. and relative) in all source files to resolve correctly under the new structure.
- [ ] Update all python import paths in the `backend/tests/` directory (e.g., `tests/test_auth.py`, `tests/test_executor.py`, `tests/conftest.py`, and `tests/integration/test_database.py`).
- [ ] Ensure the backend test suite executes fully and passes (running `make test` completes with 100% pass rate).
- [ ] Ensure formatting and linting rules pass cleanly (running `make lint` returns no ruff or formatting warnings/errors).

## Technical Constraints
(derived from sdd-specs/mission.md and sdd-specs/tech-stack.md)
- **FastAPI / Pydantic Alignment**: Restructuring must utilize standard FastAPI routing and Pydantic models for serialization, avoiding custom mapping layers or verbose abstract repositories unless strictly required.
- **Type Safety**: Maintain strict type annotations across all modified functions, methods, and modules.
- **Backward Compatibility**: Ensure that the exposed HTTP API endpoints remain completely unchanged so that the React frontend is not impacted by this backend refactoring.

## In Scope
- Creating the new `backend/app/schemas/` folder.
- Reorganizing the `backend/app/` structure (rearranging files/directories).
- Updating imports in backend files (`backend/app/` and `backend/tests/`).
- Verifying the build, test, and lint status locally.

## Out of Scope
- Modifying frontend code or frontend file structure.
- Modifying database schemas or migrations.
- Changing core business logic behavior of the auth or code executor services.

## Dependencies
- Completed Phase 1 base repository setup.
- `make` and `pytest` environments configured on the development host.

## Stakeholder Flags
- none

## Success Metrics
- Average boilerplate lines of imports/mappers per new database/endpoint entity is reduced.
- Restructured code complies fully with existing `pytest` testing suites without behavioral modifications.
- Linter and formatter execute with zero errors under the new folder structure.
