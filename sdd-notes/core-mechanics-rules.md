## Core Mechanics & Rules

1.  **Challenge Scope**: Backend coding tasks only. No frontend-specific tasks (e.g., UI visual layout or DOM manipulation) or system design diagrams.
2.  **Runtimes Supported**: Python and Node.js/TypeScript.
3.  **Time Limit**: Exactly 30 minutes. The session automatically terminates and submits when the timer hits zero.
4.  **Token Budget**: A hard cap on Gemini API tokens. The LLM proxy will block further prompts if the budget is exceeded.
5.  **Game Limit**: Restrained to exactly **1 game per user per day** to control API costs.
6.  **Submission Scope**: Single-file code submissions to keep the sandboxed runner simple.

### Scoring Formula
$$\text{Total Score} = \frac{\text{Correctness} + \text{Efficiency} + \text{Speed}}{3}$$
*   **Correctness**: $\frac{\text{Passed Unit Tests}}{\text{Total Unit Tests}} \times 100$
*   **Efficiency**: $\frac{\text{Token Budget} - \text{Tokens Used}}{\text{Token Budget}} \times 100$ (if tokens exceed budget, Efficiency is 0)
*   **Speed**: $\frac{\text{Remaining Time (seconds)}}{\text{Total Time (1800 seconds)}} \times 100$
