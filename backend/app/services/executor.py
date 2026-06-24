import json
import time
import logging
import threading
from typing import Dict, List, Union
import docker
import requests

logger = logging.getLogger("app")

_docker_client = None
_docker_client_lock = threading.Lock()

def get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        with _docker_client_lock:
            if _docker_client is None:
                _docker_client = docker.from_env()
    return _docker_client

def execute_code_locally(
    code: str,
    language: str,
    test_suite: str
) -> Dict[str, Union[str, bool, List[Dict[str, Union[str, bool]]]]]:
    """Executes the given code and test suite in a local Docker container sandbox.

    Args:
        code: The solution code string.
        language: The execution language (e.g. "python", "javascript").
        test_suite: The test suite script to verify the solution.

    Returns:
        A dict matching the standardized output schema:
        {
            "stdout": str,
            "stderr": str,
            "passed": bool,
            "test_results": list[dict]
        }
    """
    client = get_docker_client()
    container = None
    start_time = time.monotonic()

    try:
        container = client.containers.run(
            image="sandbox-lambda",
            environment={
                "LANGUAGE": language,
                "CODE": code,
                "TEST_SUITE": test_suite
            },
            network_mode="none",
            mem_limit="256m",
            nano_cpus=1000000000,
            detach=True
        )

        try:
            wait_result = container.wait(timeout=5)
            exit_code = wait_result.get("StatusCode", 0)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as timeout_err:
            duration = time.monotonic() - start_time
            logger.warning(
                "Sandbox container timed out after %.2f seconds: %s",
                duration, timeout_err
            )
            # Try to kill container immediately
            try:
                container.kill()
            except Exception as kill_err:
                logger.error("Error killing container after timeout: %s", kill_err)

            # Read whatever logs exist
            try:
                stdout_bytes = container.logs(stdout=True, stderr=False)
                stderr_bytes = container.logs(stdout=False, stderr=True)
            except Exception:
                stdout_bytes = b""
                stderr_bytes = b""

            stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

            logger.info(
                "Sandbox execution timed out. Duration: %.2fs, ExitCode: -1, Stdout: %s, Stderr: %s",
                duration, stdout_str, stderr_str
            )

            return {
                "stdout": stdout_str,
                "stderr": stderr_str or "Execution timed out after 5 seconds.",
                "passed": False,
                "test_results": [
                    {
                        "name": "timeout",
                        "passed": False,
                        "message": "Execution timed out (limit: 5s)"
                    }
                ]
            }

        # Successful container.wait run
        duration = time.monotonic() - start_time
        try:
            stdout_bytes = container.logs(stdout=True, stderr=False)
            stderr_bytes = container.logs(stdout=False, stderr=True)
        except Exception as logs_err:
            logger.error("Error retrieving logs: %s", logs_err)
            stdout_bytes = b""
            stderr_bytes = b""

        stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

        logger.info(
            "Sandbox execution completed. ExitCode: %d, Duration: %.2fs, Stdout: %s, Stderr: %s",
            exit_code, duration, stdout_str, stderr_str
        )

        parsed_result = None
        # 1. Search for a valid JSON dictionary from the bottom of stdout_str line-by-line
        lines = stdout_str.splitlines()
        for line in reversed(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('{') and stripped_line.endswith('}'):
                try:
                    candidate = json.loads(stripped_line)
                    if isinstance(candidate, dict):
                        parsed_result = candidate
                        break
                except json.JSONDecodeError:
                    pass

        # 2. Fallback to greedy curly brace extraction
        if parsed_result is None:
            start_idx = stdout_str.find('{')
            end_idx = stdout_str.rfind('}')
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_candidate = stdout_str[start_idx:end_idx+1]
                try:
                    candidate = json.loads(json_candidate)
                    if isinstance(candidate, dict):
                        parsed_result = candidate
                except json.JSONDecodeError as err:
                    logger.debug("Failed to parse JSON candidate from stdout: %s", err)

        # 3. Fallback to parsing entire stdout_str
        if parsed_result is None:
            try:
                candidate = json.loads(stdout_str)
                if isinstance(candidate, dict):
                    parsed_result = candidate
            except json.JSONDecodeError:
                parsed_result = None

        if parsed_result is not None and isinstance(parsed_result, dict):
            # Ensure test_results is a list
            raw_results = parsed_result.get("test_results")
            if not isinstance(raw_results, list):
                raw_results = []

            sanitized_results = []
            for res in raw_results:
                if isinstance(res, dict):
                    sanitized_results.append({
                        "name": str(res.get("name", "")),
                        "passed": bool(res.get("passed", False)),
                        "message": str(res.get("message", ""))
                    })

            return {
                "stdout": str(parsed_result.get("stdout", "")),
                "stderr": str(parsed_result.get("stderr", "")),
                "passed": bool(parsed_result.get("passed", False)),
                "test_results": sanitized_results
            }
        else:
            return {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "passed": False,
                "test_results": [
                    {
                        "name": "execution-failure",
                        "passed": False,
                        "message": stderr_str or f"Execution failed with exit status {exit_code}"
                    }
                ]
            }

    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception as rm_err:
                logger.error("Error removing sandbox container: %s", rm_err)
