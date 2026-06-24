# 🚀 Product Requirements Document: Prompt Arena MVP

### 1. Product Overview

* **Name:** Prompt Arena
* **Purpose:** A competitive, 30-minute timeboxed coding game where developers must write functional code using AI assistance without exceeding a strict token budget limit.
* **Target Audience:** Invited & Authenticated software engineers.
* **Goal:** Evaluate spec-driven development, context window optimization, and prompt harnessing skills in a highly engaging, token-efficient, and competitive format.

---

### 2. Tech Stack & Architecture

- User should be authenticated easily to ensure the application is only used by invited & authenticated users. (passwordless)
- Application backend should use python, specifically FastAPI.
- GCP will be used as the cloud provider.
- This application should be assessible via the web for players and spectators.
- Database is still undecided, would love your recommendation
- Users will be using an integrated terminal-like interface on the webapp to write their prompts and get responses from LLMs. or any other suggestion is welcomed


---

### 3. Core Mechanics & Rules

1. **Time Limit:** Exactly 30 minutes. The CLI automatically terminates the session and sends the scorecard when time expires.
2. **Token Budget:** A hard cap on API tokens (budget varies by difficulty). If the remaining balance hits exactly zero, the CLI immediately blocks further API requests and ends the game.
3. **Scoring Matrix:**
* **Correctness (%):** Passed unit tests divided by total Acceptance Criteria (AC).
* **Efficiency:** (`Token Budget` - `Tokens Used`) / `Token Budget` * 100
* **Speed:** Remaining time on the clock.
* **Total Score:** (Correctness + Efficiency + Speed) / 3 (opened for suggestions & recommendations)


---

### 4. User Journeys

**Player Journey (CLI):**

1. Engineer logins and joins the session. They select a difficulty level (easy, medium, or hard).
2. The CLI presents the problem statement, Acceptance Criteria (AC), and the token budget limit.
3. The engineer uses their preferred LLM tool through the CLI prompt interface to write code that satisfies the AC. The CLI logs token usage and time if possible
4. Game ends (via time, token exhaustion, or manual submission). The CLI runs the unit tests, calculates the score, and POSTs the JSON scorecard to the backend.

**Spectator Journey (Web Dashboard):**

1. Users visit the web dashboard.
2. The UI fetches the top scores from the database and displays a live leaderboard ranked by Correctness, then Efficiency, then Speed.

---

### 5. Sample Problem Statement Inventory

#### Tier 1: Easy - "The JSON Data Pipeline Sanitizer"

* **Token Budget:** 8,000 tokens
* **Scenario:** Process messy JSON logs triggered by S3 `ObjectCreated`. Strip PII and map to a new schema.
* **Evaluation Focus:** Context Squeezing. Engineers must selectively feed the AI small payload samples instead of dumping a 10MB log file into the prompt.

---
