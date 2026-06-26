# Feature Spec: Game Session & Arena Workspace

## Objective
Establish the frontend and backend workspace interface and session lifecycle orchestration to allow invited players to select a challenge, configure settings, start a timed session, code, test their solutions in a secure sandbox, and complete the challenge.

## User & Stakeholder
Invited and authenticated software engineers (players) who interact with the web workspace and simulated terminal, and system administrators who require backend-enforced timeouts and API consumption boundaries.

## Acceptance Criteria
- Given a player selects a challenge difficulty on the dashboard, when they click it, they are shown a pre-flight modal presenting the rules, selected language (Python or Node/TypeScript dropdown), token budget, and the 30-minute time constraint.
- Given a player clicks "Start Challenge" in the modal, when the game session is initialized, then:
  - An active game session is created in Supabase with a server-backed `started_at` timestamp.
  - A strict 30-minute timer begins.
  - The player is redirected to the Arena Workspace, and they cannot start another game today.
- Given an active game session, when the Arena Workspace renders, then the layout displays:
  - **Left Pane**: The challenge statement, acceptance criteria, remaining token budget (dynamically updated), and remaining time (synced to the server countdown).
  - **Middle/Right Pane**: Monaco code editor initialized with the starter file content for the selected language.
  - **Bottom Pane**: Interactive simulated terminal.
- Given a player types `run tests` in the simulated terminal, when executed, then:
  - The single-file code from Monaco editor is sent to the backend.
  - The backend runs the code securely inside the AWS Lambda sandbox (capped at 5 seconds and no network access).
  - The test results are streamed/polled back and outputted to the terminal.
- Given a player inputs a query/prompt to the LLM directly in the terminal, when executed, then:
  - The prompt is routed to the Python Gemini LLM proxy.
  - Token consumption is measured and subtracted from the challenge-specific budget.
  - If the budget is exhausted, further LLM requests are blocked.
- Given a player's active session, when game termination is triggered (via manual submission, 30-minute timer expiration, or token budget exhaustion), then:
  - The backend runs a final test suite validation.
  - The final score scorecard is computed (Correctness, Efficiency, Speed) and saved to Supabase.
  - The session is marked as completed/closed, and the user is redirected to the scorecard view.

## Technical Constraints
- The frontend and backend must strictly enforce authentication checks (Supabase Auth magic links/OTP) for starting a game and running test submissions.
- Code workspace supports single-file submissions only.
- Frontend views must not require visual layout or DOM manipulation challenge types (backend only).
- All communications with the LLM must go through the proxy to measure token counts.
- Submission code execution must run on AWS Lambda sandbox environments with network access disabled and a maximum 5-second run time.
- All session lifecycle and terminal interaction endpoints must be thoroughly unit and integration tested.

## In Scope
- React components for the "Start Challenge" pre-flight modal (language selector dropdown, instructions list).
- Three-pane Arena Workspace layout: left (challenge description, countdown timer, token budget indicator), right/middle (Monaco Editor), bottom (interactive terminal).
- Supabase game session CRUD endpoints in FastAPI backend.
- WebSocket or polling APIs for executing sandbox tests and updating the terminal outputs.
- Backend session countdown verification, ensuring users cannot submit after 30 minutes from the server-backed `started_at` time.
- Terminal commands: `run tests` and inline Gemini prompting.
- Game termination flow: automatic submission on timeout/exhaustion and manual submission.

## Out of Scope
- Public leaderboard dashboard and detailed scorecard visual layouts (designed in subsequent Phase 3 features).
- Multi-file workspace layout support.
- Supporting runtimes other than Python and Node.js/TypeScript.
- Executing user submissions directly on the backend container.

## Dependencies
- Supabase database schema for users, challenges, sessions, and scorecards (defined in sdd-specs/roadmap.md Phase 1).
- AWS Lambda sandbox runner deployment configurations (defined in sdd-specs/roadmap.md Phase 2).
- Python Gemini LLM proxy token tracking API (defined in sdd-specs/roadmap.md Phase 2).

## Stakeholder Flags
- **Timing synchronization**: The UI countdown timer must periodically re-sync with the server-tracked time to prevent local client-side manipulation of the 30-minute limit.

## Success Metrics
- Players can successfully select a language, start a challenge, edit code, run tests, and prompt the LLM.
- The 30-minute timer is strictly enforced; submissions received 1801+ seconds after session start are rejected or graded based on the last valid run.
- Token budget is deducted correctly per LLM interaction, and the terminal reflects budget exhaustion instantly.
