## Security & Sandbox Design

### AWS Lambda Executor
*   When a player runs tests, the FastAPI backend invokes a dedicated AWS Lambda function.
*   **Payload**: The user's code, the language environment (Python or Node/TS), and the test suite file.
*   **Isolation**: Lambda isolates the execution in a Firecracker microVM. Execution time is capped to 5 seconds, and network access is disabled within the execution function.
*   **Output**: Returns stdout, stderr, and the test results JSON back to the backend.