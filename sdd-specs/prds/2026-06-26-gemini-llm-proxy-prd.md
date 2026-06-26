# Product Requirement Document: Gemini LLM Proxy

## Objective & Goal
* **Problem**: Players using LLM prompts during a challenge could cause unbounded Google Gemini API billing costs. Furthermore, we must enforce token budgets to maintain game fairness (players should win through clever prompt engineering and coding rather than brute-force LLM usage). Lastly, raw Gemini API credentials must be secured.
* **Objective**: Build a secure Python-based Gemini LLM Proxy in FastAPI that routes prompt execution, counts tokens using Gemini API metadata, deducts them atomically from the player's active session budget in Supabase, and blocks requests when the budget is exhausted.
* **Why now**: We are splitting Phase 2 into two phases. Building the proxy backend first establishes the execution and billing foundation before the React workspace UI and terminal components are implemented in Phase 3.

## User Personas
* **Invited Software Engineer (Player)**: Wants to submit prompt queries to Gemini within their coding environment to get helper details, tips, or architectural advice without exceeding the challenge-specific token limit.
* **System Administrator / Creator**: Wants to ensure the platform operates within safe, predictable API budget limits and guarantees that the scoring remains competitive and fair.

## Core User Journeys
1. **Successful Prompt Execution**:
   - **Given** an active game session with a remaining token budget (e.g., 2,000 tokens),
   - **When** the player submits a text prompt,
   - **Then** the proxy forwards the prompt to Gemini 1.5 Flash, retrieves the response along with usage metadata, deducts the precise tokens used (input + output) from the session's budget in Supabase, and returns the LLM response along with the updated remaining budget.
2. **Pre-flight Block (Exhausted Budget)**:
   - **Given** an active game session where the remaining token budget is $\le 0$,
   - **When** the player attempts to submit a prompt,
   - **Then** the proxy immediately rejects the request with a `403 Forbidden` error without invoking the Gemini API.
3. **Post-execution Exhaustion (Overdraft)**:
   - **Given** a session with a small remaining budget (e.g., 30 tokens),
   - **When** the player submits a prompt, and the resulting Gemini call consumes 50 tokens,
   - **Then** the proxy writes the database entry (deducting the full amount, resulting in a negative/zero balance), returns the final response, but flags the session budget as exhausted so all future requests are blocked.

## Prioritized Requirements (MoSCoW)
* **Must Have** (Required for MVP):
  - Route text prompt requests from FastAPI backend to the Gemini API.
  - Calculate exact token consumption (prompt input tokens + candidate output tokens) using Gemini's response metadata.
  - Retrieve the current session's remaining budget from Supabase before executing LLM calls.
  - Enforce atomic database updates (e.g., direct atomic subtraction in PostgreSQL) to prevent budget bypasses via concurrent requests.
  - Return a standard error response (`403 Forbidden`) when the budget is fully exhausted.
  - Impose a strict 10-second timeout on Gemini API requests.
* **Should Have** (High value, can defer if tight timeline):
  - Inject custom system instruction wrappers (e.g., "Do not output direct complete code solutions, guide the user algorithmically") to prevent players from asking the LLM to write the exact challenge solution.
  - Handle rate limits (`429 Too Many Requests`) and transient errors from Gemini gracefully, returning readable terminal errors to the user without failing the game session.
* **Could Have** (Nice-to-have, low priority):
  - Log token usage transactions in a lightweight audit table (recording timestamp, session ID, input tokens, output tokens, model version).
* **Won't Have** (Out of scope for this release):
  - Storing full prompt/response chat history text in the database.
  - Prompt caching.
  - Response streaming (non-streaming text response is sufficient for the terminal UI).
  - Multi-model selection (standardize on Gemini 1.5 Flash).

## Technical & Non-Functional Constraints
* **Gemini Client**: Must use the official Google Generative AI SDK in Python.
* **Key Security**: The `GEMINI_API_KEY` must be loaded from backend environment variables and must never be exposed to the client application.
* **DB Atomicity**: Token subtraction must be done atomically to avoid race conditions.
* **Input Validation**: Text prompts must be sanitized and capped at a maximum of 10,000 characters per request.
* **Performance**: The proxy logic overhead (pre-check and post-save DB transactions) must be $\le 100\text{ms}$ under standard database loads.

## Out of Scope (Non-Goals)
* Developing Monaco Editor UI layouts, terminal UI components, and websocket clients (deferred to Phase 3).
* Deploying the AWS Lambda sandbox execution environment (handled separately in the Lambda Runner spec).

## Risks & Dependencies
* **Dependencies**: 
  - FastAPI backend.
  - Supabase client and PostgreSQL database schema.
  - Google Gemini API.
* **Risks**:
  - Gemini API rate limits could be hit during high-traffic events, impacting user experience.
  - Network latency between AWS and Google Gemini servers could cause occasional request delays.

## Success Metrics
* **Zero Token Leakage**: No game session can consume more than 100% of its allocated token budget.
* **Key Confidentiality**: Zero instances of Gemini API key leaks to frontend network requests.
* **Low Proxy Overhead**: Latency added by proxy checks/database updates is $\le 100\text{ms}$.
