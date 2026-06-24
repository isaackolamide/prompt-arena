from backend.app.services.executor import execute_code_locally

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
