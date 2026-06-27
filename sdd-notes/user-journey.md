## User Journeys

### Player Journey
1.  **Authentication**: Player logs in via a Magic Link.
2.  **Dashboard**: Player views the active leaderboard and selects a difficulty level (Easy, Medium, Hard). If they've already played their daily game, they cannot start a new one.
3.  **Pre-Flight Setup & Start**: The player selects their language (Python or Node/TypeScript). They are presented with a "Start Challenge" modal explaining the rules, token budget, and 30-minute time constraint. Clicking **"Start Challenge"** sends a request to the backend, creating a active game session in Supabase with a server-backed `started_at` timestamp. This initiates the timer.
4.  **Arena Workspace**:
    *   **Left Pane**: Challenge statement, acceptance criteria, remaining token budget, and remaining time (synced to the server-tracked countdown).
    *   **Middle/Right Pane**: Monaco code editor displaying the starter file.
    *   **Bottom Pane**: Simulated terminal. Players can type `run tests` (which uploads the code to the backend, executes it in AWS Lambda, and outputs test results) or prompt the LLM directly in the terminal to request assistance.
5.  **Game Termination**: Triggered by manual submission, time expiration, or token budget exhaustion. The final test suite is run, the score is calculated, and the scorecard is saved in Supabase.