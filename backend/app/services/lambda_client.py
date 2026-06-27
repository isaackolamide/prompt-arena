import asyncio
import json
import logging
import time
import traceback
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from app.core.config import Settings

logger = logging.getLogger("app")


class SandboxTimeoutError(Exception):
    """Raised when sandbox execution times out."""

    pass


class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails due to network or AWS errors."""

    pass


def log_event(event_name: str, **kwargs: Any) -> None:
    """Emits structured JSON log events."""
    log_data = {"event": event_name, **kwargs}
    logger.info(json.dumps(log_data))


class LambdaClient:
    """Client for invoking AWS Lambda sandbox service."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Configure Boto3 config with safety timeouts to avoid hanging indefinitely
        config = Config(
            connect_timeout=5.0,
            read_timeout=15.0,
            retries={"max_attempts": 0},
        )
        self.client = boto3.client(
            "lambda",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_LAMBDA_ENDPOINT_URL,
            config=config,
        )

    async def execute_in_sandbox(
        self, code: str, test_suite: str, language: str
    ) -> dict[str, Any]:
        """Invokes AWS Lambda sandbox function synchronously and returns result.

        Args:
            code: Solution code to run.
            test_suite: Test suite code to verify solution.
            language: Target runtime language (e.g. "python", "javascript").

        Returns:
            Dict containing stdout, stderr, passed, and test_results.

        Raises:
            SandboxTimeoutError: If execution times out.
            SandboxExecutionError: If execution fails on AWS or network.
        """
        start_time = time.monotonic()

        log_event(
            "sandbox_run_started",
            language=language,
            code_length=len(code),
            test_suite_length=len(test_suite),
        )

        try:
            payload = {
                "language": language,
                "code": code,
                "test_suite": test_suite,
            }

            # Invoke lambda synchronously, offloaded to thread to avoid blocking loop
            response = await asyncio.to_thread(
                self.client.invoke,
                FunctionName=self.settings.AWS_LAMBDA_FUNCTION_NAME,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload).encode("utf-8"),
            )

            duration = time.monotonic() - start_time

            # Handle execution-level error indicated by Lambda
            if "FunctionError" in response:
                payload_bytes = response["Payload"].read()
                payload_str = payload_bytes.decode("utf-8")
                try:
                    error_data = json.loads(payload_str)
                    error_msg = error_data.get("errorMessage", payload_str)
                except json.JSONDecodeError:
                    error_msg = payload_str

                if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise SandboxTimeoutError(
                        f"Sandbox execution timed out: {error_msg}"
                    )
                else:
                    raise SandboxExecutionError(
                        f"Sandbox execution failed: {error_msg}"
                    )

            # Safely parse response payload
            payload_bytes = response["Payload"].read()
            payload_str = payload_bytes.decode("utf-8")
            try:
                result = json.loads(payload_str)
            except json.JSONDecodeError as e:
                raise SandboxExecutionError(
                    f"Failed to parse sandbox response JSON: {str(e)}"
                )

            if not isinstance(result, dict):
                raise SandboxExecutionError(
                    "Sandbox response payload is not a JSON object"
                )

            # Validate returned dictionary keys and types
            for key in ("stdout", "stderr", "passed", "test_results"):
                if key not in result:
                    raise SandboxExecutionError(
                        f"Missing required key '{key}' in sandbox response"
                    )

            if not isinstance(result["stdout"], str):
                raise SandboxExecutionError("Invalid 'stdout' type in response")
            if not isinstance(result["stderr"], str):
                raise SandboxExecutionError("Invalid 'stderr' type in response")
            if not isinstance(result["passed"], bool):
                raise SandboxExecutionError("Invalid 'passed' type in response")
            if not isinstance(result["test_results"], list):
                raise SandboxExecutionError("Invalid 'test_results' type in response")

            # Count passed/failed tests
            test_results = result["test_results"]
            passed_count = 0
            failed_count = 0
            for t in test_results:
                if isinstance(t, dict) and t.get("passed") is True:
                    passed_count += 1
                else:
                    failed_count += 1

            exit_status = response.get("StatusCode", 200)

            log_event(
                "sandbox_run_completed",
                passed_count=passed_count,
                failed_count=failed_count,
                duration=duration,
                exit_status=exit_status,
                passed=result["passed"],
            )

            return {
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "passed": result["passed"],
                "test_results": result["test_results"],
            }

        except (ReadTimeoutError, SandboxTimeoutError) as e:
            duration = time.monotonic() - start_time
            error_msg = str(e)
            tb = traceback.format_exc()
            log_event(
                "sandbox_run_failed",
                error=error_msg,
                traceback=tb,
                duration=duration,
            )
            if isinstance(e, SandboxTimeoutError):
                raise
            raise SandboxTimeoutError(f"Sandbox execution timed out: {error_msg}")

        except ConnectTimeoutError as e:
            duration = time.monotonic() - start_time
            error_msg = str(e)
            tb = traceback.format_exc()
            log_event(
                "sandbox_run_failed",
                error=error_msg,
                traceback=tb,
                duration=duration,
            )
            raise SandboxExecutionError(
                f"AWS Lambda connection timed out: {error_msg}"
            )

        except ClientError as e:
            duration = time.monotonic() - start_time
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            tb = traceback.format_exc()
            log_event(
                "sandbox_run_failed",
                error=f"ClientError({error_code}): {error_msg}",
                traceback=tb,
                duration=duration,
            )
            raise SandboxExecutionError(
                f"AWS Lambda client error ({error_code}): {error_msg}"
            )

        except Exception as e:
            duration = time.monotonic() - start_time
            error_msg = str(e)
            tb = traceback.format_exc()
            log_event(
                "sandbox_run_failed",
                error=error_msg,
                traceback=tb,
                duration=duration,
            )
            if isinstance(e, SandboxExecutionError):
                raise
            raise SandboxExecutionError(f"Sandbox execution failed: {error_msg}")
