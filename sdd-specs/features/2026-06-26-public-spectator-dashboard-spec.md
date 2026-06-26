# Feature Spec: Public Spectator Dashboard

## Objective
Design and implement a public, unauthenticated landing dashboard featuring a live-updating leaderboard of coding tournament results and detailed scorecard inspectors showing submission code and execution performance.

## User & Stakeholder
Public spectators (visitors without accounts), tournament players who want to check their rank, and administrators who want to showcase top performers.

## Acceptance Criteria
- Given an unauthenticated visitor, when they load the application URL, then they are presented with the public spectator dashboard without being prompted to log in.
- Given the public spectator dashboard, when loaded, then:
  - It fetches scorecard data from the database and renders a leaderboard table.
  - The table is sorted by Total Score in descending order.
  - It displays player username/name, total score, correctness %, token efficiency %, and completion speed %.
- Given a row in the leaderboard table, when a spectator clicks on it, then they are navigated to a read-only scorecard detail page.
- Given the scorecard detail page, when displayed, then it renders:
  - Player metadata (username, challenge name, date/time completed).
  - Scorecard metrics (Correctness, Efficiency, Speed, and final computed Total Score).
  - The specific challenge description and difficulty level.
  - The complete, raw, single-file code submission with syntax highlighting (Python or Node/TypeScript).
  - A visual breakdown of passed vs total unit tests.
  - Token consumption stats (Tokens Used out of the Token Budget).

## Technical Constraints
- The dashboard views (leaderboard and scorecard details) must be fully public and accessible without any authentication.
- API endpoints supplying public leaderboard information and scorecard details must be read-only (`GET` requests only) and contain no sensitive user secrets or private profile information.
- Public scorecard viewer must render player code submissions securely (safe text rendering, no execution or HTML Injection vulnerabilities).
- Layout and elements must be fully responsive to accommodate mobile, tablet, and desktop screens.
- Implement robust unit/integration tests for the public dashboard components and API endpoints.

## In Scope
- Web UI for the public dashboard hosting the tournament leaderboard.
- Dynamic sorting, filtering (by language, difficulty, or date), and search functionality on the leaderboard table.
- Scorecard detail inspector page showing code submissions, token usage graphs, and test execution details.
- FastAPI backend routes for `GET /api/leaderboard` and `GET /api/scorecards/{id}`.
- Database queries targeting Supabase `scorecards` view/table with pagination support.

## Out of Scope
- Authenticated player actions (starting games, submitting solutions, requesting LLM prompts) on this dashboard.
- Designing or managing administrative whitelists or player signups.
- Execution or rerun capability of scorecard code submissions from the spectator view.

## Dependencies
- Phase 1 Supabase DB schema for `scorecards` and `profiles` tables (defined in sdd-specs/roadmap.md Phase 1).
- Phase 3 Core Game Mechanics & Scoring backend (defined in sdd-specs/roadmap.md Phase 3) for persisting computed scorecards.

## Stakeholder Flags
- **Caching of Leaderboard**: To prevent Supabase query database overload from high spectator traffic, the backend `GET /api/leaderboard` query results should be cached for 60 seconds.

## Success Metrics
- Spectators can view the live leaderboard and detail scorecards without being authenticated or having to sign up.
- The leaderboard accurately lists and ranks all completed game sessions.
- Detailed scorecard views correctly display the exact unit test pass rate, proxy-tracked token usage, and the submitted source file.
