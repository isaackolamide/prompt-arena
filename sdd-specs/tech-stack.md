# Tech Stack & Implementation

## Project Structure

```
backend/                → FastAPI application source code (Python)
backend/app/            → API routes, Supabase client, LLM proxy, and sandbox trigger
backend/tests/          → pytest suite for backend endpoints and mocks
frontend/               → Vite + React/TS application source code
frontend/src/           → UI views, Monaco editor components, and terminal simulation
frontend/src/tests/     → Vitest suite for React component testing
sandbox-lambda/         → AWS Lambda runner code (Firecracker microVM executions)
sdd-specs/              → Specification documents (mission, tech-stack, roadmap)
```

## Code Style

### Naming Conventions

#### TypeScript (Frontend)
- Files: `PascalCase.tsx` for React components, `camelCase.ts` for helper scripts, `name.test.tsx` or `name.test.ts` for tests
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Classes/Types/Interfaces: `PascalCase`

#### Python (Backend)
- Files: `snake_case.py` for all source files, `test_*.py` for test files
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`

### Formatting Rules

- Indentation: 2 spaces for TypeScript/HTML/CSS; 4 spaces for Python
- Line length: 100 characters max for TypeScript; 88 characters max for Python (Ruff default)

### Examples

```typescript
// TypeScript (Good)
export interface UserProfile {
  userId: string;
  dailyGameCount: number;
}

export function calculateScore(correctness: number, efficiency: number, speed: number): number {
  return (correctness + efficiency + speed) / 3;
}
```

```python
# Python (Good)
from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: str
    daily_game_count: int

def calculate_score(correctness: float, efficiency: float, speed: float) -> float:
    return (correctness + efficiency + speed) / 3.0
```

## Testing Strategy

For detailed implementation guidelines (AAA structure, mocks, and builders), refer to the shared `harnesspowers:references/testing-patterns.md` reference.

### Framework & Tools

#### Backend
- Test Runner: `pytest`
- Assertion Library: Pytest built-in assertions
- Coverage Target: 80%

#### Frontend
- Test Runner: `vitest`
- Assertion Library: Vitest assertions with React Testing Library
- Coverage Target: 80%

### TDD & Mocking Conventions
- **TDD Cycle**: Follow Red-Green-Refactor. Always write a failing test before introducing logic.
- **Mock Boundaries**: Mock database (Supabase) calls, external LLM API calls, and AWS Lambda executor HTTP invocations. Never mock pure scoring functions, budget validators, or core domain logic.
- **Builder Pattern**: Use builder classes (e.g. `GameSessionBuilder`) to construct complex objects and mock values in test setups to protect tests against schema changes.

### Test Organization

Tests live in:
- Backend: `backend/tests/`
- Frontend: `frontend/src/tests/` or alongside source components as `[name].test.tsx`
- Sandbox: `sandbox-lambda/tests/`

### Test Levels

- **Unit**: Test individual React components, utility hooks, FastAPI services, and prompt calculators.
- **Integration**: Test full API request-response cycles, Supabase client operations, and external system handlers.
- **E2E**: Critical flows only (e.g., Auth sign-in -> start challenge -> submit challenge -> scorecard displayed).
