from backend.app.services.executor import execute_code_locally
import requests

def test_python_success():
    """Verify that a correct Python script passes assertion tests."""
    code = "def add(a, b):\n    return a + b\n"
    test_suite = (
        "from solution import add\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n"
    )
    res = execute_code_locally(code=code, language="python", test_suite=test_suite)
    assert res["passed"] is True
    assert len(res["test_results"]) > 0
    assert res["test_results"][0]["passed"] is True

def test_python_failure():
    """Verify that a failing Python script fails assertions."""
    code = "def add(a, b):\n    return a + b\n"
    test_suite = (
        "from solution import add\n"
        "def test_add():\n"
        "    assert add(1, 2) == 4\n"
    )
    res = execute_code_locally(code=code, language="python", test_suite=test_suite)
    assert res["passed"] is False
    assert len(res["test_results"]) > 0
    assert res["test_results"][0]["passed"] is False

def test_javascript_success():
    """Verify that a correct JavaScript script passes assertions."""
    code = "export function add(a, b) {\n    return a + b;\n}\n"
    test_suite = (
        "import test from 'node:test';\n"
        "import assert from 'node:assert';\n"
        "import { add } from './solution.js';\n"
        "test('add success', () => {\n"
        "    assert.strictEqual(add(1, 2), 3);\n"
        "});\n"
    )
    res = execute_code_locally(code=code, language="javascript", test_suite=test_suite)
    assert res["passed"] is True
    assert len(res["test_results"]) > 0
    assert res["test_results"][0]["passed"] is True

def test_javascript_failure():
    """Verify that a failing JavaScript script fails assertions."""
    code = "export function add(a, b) {\n    return a + b;\n}\n"
    test_suite = (
        "import test from 'node:test';\n"
        "import assert from 'node:assert';\n"
        "import { add } from './solution.js';\n"
        "test('add failure', () => {\n"
        "    assert.strictEqual(add(1, 2), 4);\n"
        "});\n"
    )
    res = execute_code_locally(code=code, language="javascript", test_suite=test_suite)
    assert res["passed"] is False
    assert len(res["test_results"]) > 0
    assert res["test_results"][0]["passed"] is False

def test_timeout_limit():
    """Verify that code taking longer than 5 seconds is timed out, killed, and cleaned up."""
    # Python script that sleeps for 10 seconds
    code = "import time\ntime.sleep(10)\n"
    test_suite = ""  # direct execution
    res = execute_code_locally(code=code, language="python", test_suite=test_suite)
    assert res["passed"] is False
    # Check if timeout is reported or parsed failing results
    assert any(
        "timeout" in str(t.get("name", "")).lower() or "timeout" in str(t.get("message", "")).lower()
        for t in res["test_results"]
    )

def test_network_block():
    """Verify that the container network is blocked (network_mode='none') and requests fail."""
    # Python code attempting to make a network request
    code = (
        "import urllib.request\n"
        "try:\n"
        "    urllib.request.urlopen('https://example.com', timeout=3)\n"
        "except Exception as e:\n"
        "    print(f'NETWORK_ERROR: {e}')\n"
        "    raise\n"
    )
    test_suite = ""  # direct execution
    res = execute_code_locally(code=code, language="python", test_suite=test_suite)
    assert res["passed"] is False
    # The message should contain info about network/resolution failure or URLError
    stderr = res.get("stderr", "")
    stdout = res.get("stdout", "")
    assert "NETWORK_ERROR" in stdout or "urllib.error.URLError" in stderr or "URLError" in stdout or "URLError" in stderr

def test_executor_json_extraction_and_sanitization():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    
    # Configure container mock
    mock_container.wait.return_value = {"StatusCode": 0}
    
    # Let's test stdout pollution and type coercion
    # stdout has some printed dictionary, then some random text, then the actual output on the last line
    polluted_stdout = (
        "Some debug printed info: {'key': 'value'}\n"
        "Another line with {unbalanced brace\n"
        '{"stdout": "actual stdout", "stderr": "actual stderr", "passed": "true", "test_results": [{"name": "test1", "passed": 1, "message": "msg1"}]}\n'
    )
    
    mock_container.logs.side_effect = lambda stdout, stderr: (
        polluted_stdout.encode("utf-8") if stdout else b"mocked stderr logs"
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    # Check that it extracted the last line and coerced "true" to True, and 1 to True
    assert res["passed"] is True
    assert res["stdout"] == "actual stdout"
    assert res["stderr"] == "actual stderr"
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "test1"
    assert res["test_results"][0]["passed"] is True
    assert res["test_results"][0]["message"] == "msg1"
    
    # Verify mock container clean up was called
    mock_container.remove.assert_called_once_with(force=True)

def test_executor_fallback_greedy_and_entire_string():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}

    # Case A: Greedy curly brace extraction
    stdout_case_a = "Prefix {\"stdout\": \"ok\", \"passed\": true, \"test_results\": []} suffix"
    mock_container.logs.side_effect = lambda stdout, stderr: (
        stdout_case_a.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
    assert res["passed"] is True
    assert res["stdout"] == "ok"
    
    # Case B: Entire string parsing fallback
    stdout_case_b = '{"stdout": "entire", "passed": true, "test_results": []}'
    mock_container.logs.side_effect = lambda stdout, stderr: (
        stdout_case_b.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
    assert res["passed"] is True
    assert res["stdout"] == "entire"

def test_executor_parsing_failure():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}

    stdout_invalid = "This is not json { at all"
    mock_container.logs.side_effect = lambda stdout, stderr: (
        stdout_invalid.encode("utf-8") if stdout else b"some error"
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
    assert res["passed"] is False
    assert res["stdout"] == "This is not json { at all"
    assert res["stderr"] == "some error"
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "execution-failure"

def test_get_docker_client_thread_safety():
    from unittest.mock import patch
    import threading
    import backend.app.services.executor
    from backend.app.services.executor import get_docker_client
    
    with patch("docker.from_env") as mock_from_env:
        mock_from_env.return_value = "mock_client"
        
        # Reset singleton state
        backend.app.services.executor._docker_client = None
        
        clients = []
        threads = []
        def target():
            clients.append(get_docker_client())
            
        for _ in range(5):
            t = threading.Thread(target=target)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        assert len(clients) == 5
        assert all(c == "mock_client" for c in clients)
        # from_env should only be called once
        mock_from_env.assert_called_once()


def test_docker_exception_handling():
    from unittest.mock import MagicMock, patch
    import docker.errors
    
    mock_client = MagicMock()
    # Mock containers.run to raise DockerException
    mock_client.containers.run.side_effect = docker.errors.DockerException("Mocked Docker error")
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="print('hello')", language="python", test_suite="")
        
    assert res["passed"] is False
    assert "Mocked Docker error" in res["stderr"]
    assert "Docker execution error:" in res["stderr"]
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "docker-error"
    assert res["test_results"][0]["passed"] is False
    assert "Mocked Docker error" in res["test_results"][0]["message"]


def test_executor_requests_timeout_handling():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    
    mock_container.wait.side_effect = requests.exceptions.Timeout("Connection timed out")
    mock_container.logs.side_effect = lambda stdout, stderr: (
        b"mocked stdout logs" if stdout else b"mocked stderr logs"
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert res["stdout"] == "mocked stdout logs"
    assert res["stderr"] == "mocked stderr logs"
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "timeout"
    assert res["test_results"][0]["message"] == "Execution timed out (limit: 5s)"
    mock_container.kill.assert_called_once()


def test_executor_parsing_failure_exit_0_empty_stderr():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}

    stdout_invalid = "This is not json at all"
    mock_container.logs.side_effect = lambda stdout, stderr: (
        stdout_invalid.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert res["stdout"] == "This is not json at all"
    assert res["stderr"] == ""
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "execution-failure"
    assert res["test_results"][0]["message"] == "Failed to parse test execution output JSON"


def test_executor_parsing_failure_exit_non_zero_empty_stderr():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 127}

    stdout_invalid = "This is not json at all"
    mock_container.logs.side_effect = lambda stdout, stderr: (
        stdout_invalid.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert res["stdout"] == "This is not json at all"
    assert res["stderr"] == ""
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "execution-failure"
    assert res["test_results"][0]["message"] == "Execution failed with exit status 127"


def test_executor_wait_api_error():
    from unittest.mock import MagicMock, patch
    import docker.errors
    
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    
    # Mock container.wait to raise docker.errors.APIError
    api_error = docker.errors.APIError("Connection lost", response=None)
    mock_container.wait.side_effect = api_error
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert "Connection lost" in res["stderr"]
    assert "Docker execution error:" in res["stderr"]
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "docker-error"
    assert res["test_results"][0]["passed"] is False
    assert "Connection lost" in res["test_results"][0]["message"]
    
    # Verify cleanup was still called
    mock_container.remove.assert_called_once_with(force=True)


def test_executor_ignores_invalid_user_json():
    from unittest.mock import MagicMock, patch
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}

    # Case A: User script outputs standard printed dictionary without test_results
    polluted_stdout_no_test_results = '{"key": "value"}\n'
    mock_container.logs.side_effect = lambda stdout, stderr: (
        polluted_stdout_no_test_results.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert res["stdout"] == '{"key": "value"}'
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "execution-failure"
    assert "Failed to parse" in res["test_results"][0]["message"]

    # Case B: User script outputs JSON with test_results that is not a list
    polluted_stdout_invalid_test_results_type = '{"test_results": "not a list"}\n'
    mock_container.logs.side_effect = lambda stdout, stderr: (
        polluted_stdout_invalid_test_results_type.encode("utf-8") if stdout else b""
    )
    
    with patch("backend.app.services.executor.get_docker_client", return_value=mock_client):
        res = execute_code_locally(code="dummy", language="python", test_suite="dummy")
        
    assert res["passed"] is False
    assert res["stdout"] == '{"test_results": "not a list"}'
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "execution-failure"
    assert "Failed to parse" in res["test_results"][0]["message"]



