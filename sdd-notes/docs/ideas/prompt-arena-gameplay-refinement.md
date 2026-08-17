# Prompt Arena Gameplay Refinement: The Spec-Driven Orchestrator

## Problem Statement
How might we design a competitive coding game (Prompt Arena) where developers act as agentic engineers, coordinating and harnessing an LLM to build/modify a multi-file project workspace to pass unit tests under strict token/credit budgets?

## Recommended Direction
We are pivoting the core game loop away from manual coding to focus entirely on **Agentic Engineering**. Instead of the player typing code directly in Monaco, they act as an orchestrator. They are given a complex, "LLM-unfriendly" problem statement and a set of acceptance criteria. The player prompts the LLM to create specs, plans, and compile the final code across a multi-file directory tree.

This introduces a high-leverage strategic trade-off:
* **The Lazy Prompt Path (High Risk/High Cost)**: The player copy-pastes raw instructions directly to the LLM. The LLM generates buggy or incomplete code, leading to compilation and test failures. The player is forced into a loop of expensive debug prompts, burning their credit budget.
* **The Agentic Path (Low Risk/Low Cost)**: The player prompts the LLM to first write a structured `spec.md` and detailed execution plan. They refine this plan, toggle context files selectively, and prompt the LLM to compile. The resulting code passes in 1–2 high-precision iterations, saving credits.

## Key Assumptions to Validate
- [ ] **Challenge Complexity**: The challenges must be complex enough that simple one-liner prompts to the LLM fail, requiring detailed spec guidance or custom structures.
- [ ] **Context Selection Mechanics**: The UI must make it intuitive to choose which files are attached to the LLM context to manage input token counts.
- [ ] **Credit/Token Calibration**: The cost multiplier for input context (especially large files) must be high enough to penalize lazy copy-pasting of the entire codebase on every prompt.

## MVP Scope
* **Workspace Explorer**: Virtual file tree panel showing active project files (e.g., source code, test specs, and configuration).
* **Context Toggles**: Checkboxes next to each file to include/exclude it from the LLM prompt payload.
* **Prompt Console**: Input field supporting streaming SSE responses from the LLM, displaying compile logs, and showing credit deductions in real-time.
* **Multi-File Write Capability**: The LLM must be able to target and modify multiple files in the sandbox workspace based on the prompt.

## Not Doing (and Why)
* **Direct Player Code Editing**: We are locking the Monaco editor to read-only for the player. The player *cannot* manually patch code; they must get the LLM to do it. This preserves the pure prompt/orchestration focus of the game.
* **Real-time Collaboration**: Deferred to keep focus on single-player competitive challenges.

## Open Questions
* How do we display diffs to the player so they can easily see what changes the LLM has made to the files before running the tests?
* Should the player be able to manually write a custom local test file to assert things before running the official remote test suite?

---

## Proposed Challenge Scenarios

### 1. The Multi-Tenant Event Broker with Schema Registry (TypeScript)
* **Files**: `src/broker.ts`, `src/registry.ts`, `src/types.ts`, `tests/broker.test.ts`
* **Scenario**: Implement a message broker that routes messages based on dynamic client-defined topic schemas. The registry must compile and validate incoming JSON payloads against a custom subset of JSON Schema (supporting `$ref` local references).
* **LLM Vulnerability**: Naive prompts fail to resolve recursive `$ref` keys correctly, leading to stack overflows or API violations in code generation.

### 2. The Custom Chunked Transfer Protocol Parser (Python)
* **Files**: `protocol/parser.py`, `protocol/exceptions.py`, `protocol/connection.py`, `tests/test_protocol.py`
* **Scenario**: Implement a stateful parser for a custom binary-over-TCP protocol that transmits data in variable-sized chunks. It must handle message checksums, missing chunk flags, duplicate chunks, out-of-order delivery, and reassembly.
* **LLM Vulnerability**: LLMs struggle with stateful bitwise parsing and binary unpacking over multiple messages without a state transition outline.

### 3. Concurrent Task Scheduler with Dependency Graphs (TypeScript)
* **Files**: `scheduler/index.ts`, `scheduler/worker.ts`, `scheduler/graph.ts`, `tests/scheduler.test.ts`
* **Scenario**: Build a task runner that executes asynchronous jobs. Jobs have explicit dependencies (DAG - Directed Acyclic Graph) and execution weights. The scheduler must run independent tasks in parallel up to a concurrency limit.
* **LLM Vulnerability**: Naive prompts result in deadlocks, cycle-detection bugs, or race conditions during topological sorting.

### 4. The Virtual Filesystem & Transaction Engine (Python)
* **Files**: `fs/vfs.py`, `fs/transaction.py`, `fs/errors.py`, `tests/test_fs.py`
* **Scenario**: Implement an in-memory virtual filesystem that supports atomic file transactions (`begin`, `commit`, `rollback`). If any file operation fails within a transaction, all modifications must rollback.
* **LLM Vulnerability**: The LLM will write a naive dictionary without deep-copying metadata or handling transaction state locks, leading to dirty reads.

### 5. Dynamic Rules Engine with Expression Evaluator (TypeScript)
* **Files**: `engine/parser.ts`, `engine/evaluator.ts`, `engine/context.ts`, `tests/engine.test.ts`
* **Scenario**: Implement an engine that parses custom logical rules (e.g., `(user.age > 18 AND user.country == 'US') OR user.is_admin == true`) into an AST and evaluates them against user profiles.
* **LLM Vulnerability**: Writing tokenization and AST parsing in one go leads to operator precedence errors and whitespace parsing failures.
