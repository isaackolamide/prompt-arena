import os
import sys
import json
import time
import pytest

# Add the sandbox-lambda directory to sys.path to allow importing runner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import runner

def test_detect_esm():
    # Standard ESM import/export statements
    assert runner.detect_esm("import { add } from './solution.js';") is True
    assert runner.detect_esm("export const add = (a, b) => a + b;") is True
    assert runner.detect_esm("import 'foo';") is True
    assert runner.detect_esm("import('dynamic')") is True
    assert runner.detect_esm("export default class Foo {}") is True
    assert runner.detect_esm("export { add };") is True
    assert runner.detect_esm("  export async function foo() {}") is True
    
    # CommonJS and non-ESM patterns
    assert runner.detect_esm("const add = require('./solution');") is False
    assert runner.detect_esm("module.exports = { add };") is False
    assert runner.detect_esm("// import { add } from './solution';") is False
    assert runner.detect_esm("const s = 'import statement';") is False

    # Comments stripping cases
    assert runner.detect_esm(
        "// import { add } from './solution';\n"
        "const add = require('./solution');"
    ) is False
    assert runner.detect_esm(
        "/* import { add } from './solution'; */\n"
        "const add = require('./solution');"
    ) is False
    assert runner.detect_esm(
        "/*\nimport { add } from './solution';\n*/\n"
        "const add = require('./solution');"
    ) is False
    assert runner.detect_esm(
        "// comment\nimport { add } from './solution';"
    ) is True
    assert runner.detect_esm(
        "/* block comment */ import { add } from './solution';"
    ) is True

def test_format_node_error():
    # 1. Non-dict error_info
    assert runner.format_node_error("some error string") == "some error string"
    assert runner.format_node_error(None) == "Test failed"
    
    # 2. Dict with message
    assert runner.format_node_error({"message": "Something went wrong"}) == "Something went wrong"
    
    # 3. Cause dict with message
    assert runner.format_node_error({"cause": {"message": "Cause message"}}) == "Cause message"
    
    # 4. Assertion error format
    assert runner.format_node_error({
        "cause": {
            "code": "ERR_ASSERTION",
            "actual": 1,
            "expected": 2,
            "operator": "strictEqual"
        }
    }) == "AssertionError: Expected 2 strictEqual 1 (failed)"
    
    # 5. Failure type / code fallback
    assert runner.format_node_error({
        "code": "ERR_TEST_FAILURE",
        "failureType": "testCodeFailure"
    }) == "ERR_TEST_FAILURE: testCodeFailure"
    
    # 6. Stack fallback
    assert runner.format_node_error({"stack": "Stack details"}) == "Stack details"

def test_parse_node_json_report_pass_and_fail(tmp_path):
    report_file = tmp_path / "report.json"
    
    lines = [
        json.dumps({"type": "test:start", "data": {"name": "suite"}}),
        json.dumps({"type": "test:pass", "data": {"name": "test_pass_1"}}),
        json.dumps({"type": "test:fail", "data": {
            "name": "test_fail_1",
            "details": {
                "error": {
                    "message": "Assertion failed: 1 == 2",
                    "stack": "Error: Assertion failed: 1 == 2\n    at test_suite.js:10:5"
                }
            }
        }}),
        json.dumps({"type": "test:fail", "data": {
            "name": "test_fail_no_details",
            "error": {
                "message": "Only error message direct"
            }
        }})
    ]
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    overall_passed, results = runner.parse_node_json_report(str(report_file))
    assert overall_passed is False
    assert len(results) == 3
    
    assert results[0] == {"name": "test_pass_1", "passed": True, "message": ""}
    assert results[1] == {
        "name": "test_fail_1",
        "passed": False,
        "message": "Assertion failed: 1 == 2"
    }
    assert results[2] == {
        "name": "test_fail_no_details",
        "passed": False,
        "message": "Only error message direct"
    }

def test_parse_node_json_report_with_stderr(tmp_path):
    report_file = tmp_path / "report.json"
    
    lines = [
        json.dumps({"type": "test:stderr", "data": {"message": "SyntaxError: Unexpected token\n"}}),
        json.dumps({"type": "test:stderr", "data": {"message": "    at parse (file.js:1)\n"}}),
        json.dumps({"type": "test:fail", "data": {
            "name": "test_fail_with_stderr",
            "details": {
                "error": {
                    "code": "ERR_TEST_FAILURE",
                    "failureType": "testCodeFailure"
                }
            }
        }}),
        json.dumps({"type": "test:stderr", "data": {"message": "Some other stderr message\n"}}),
        json.dumps({"type": "test:pass", "data": {"name": "test_pass_after_stderr"}})
    ]
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    overall_passed, results = runner.parse_node_json_report(str(report_file))
    assert overall_passed is False
    assert len(results) == 2
    
    assert results[0]["name"] == "test_fail_with_stderr"
    assert results[0]["passed"] is False
    assert "SyntaxError: Unexpected token" in results[0]["message"]
    assert "Console Stderr:" in results[0]["message"]
    
    assert results[1]["name"] == "test_pass_after_stderr"
    assert results[1]["passed"] is True
    assert results[1]["message"] == ""

def test_parse_pytest_report(tmp_path):
    report_file = tmp_path / "report.json"
    
    data = {
        "exitcode": 1,
        "collectors": [
            {"nodeid": "test_suite.py", "outcome": "passed"},
            {"nodeid": "bad_syntax.py", "outcome": "failed", "longrepr": "SyntaxError: invalid syntax"}
        ],
        "tests": [
            {"nodeid": "test_suite.py::test_ok", "outcome": "passed"},
            {
                "nodeid": "test_suite.py::test_fail",
                "outcome": "failed",
                "call": {
                    "crash": {
                        "message": "assert 1 == 2"
                    }
                }
            }
        ]
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    overall_passed, results = runner.parse_pytest_report(str(report_file))
    assert overall_passed is False
    assert len(results) == 3
    
    res_dict = {r["name"]: r for r in results}
    assert res_dict["collection::bad_syntax.py"]["passed"] is False
    assert res_dict["collection::bad_syntax.py"]["message"] == "SyntaxError: invalid syntax"
    
    assert res_dict["test_suite.py::test_ok"]["passed"] is True
    assert res_dict["test_suite.py::test_fail"]["passed"] is False
    assert res_dict["test_suite.py::test_fail"]["message"] == "assert 1 == 2"

def test_parse_reports_missing_file():
    overall_passed, results = runner.parse_node_json_report("nonexistent_report.json")
    assert overall_passed is False
    assert results == []
    
    overall_passed, results = runner.parse_pytest_report("nonexistent_report.json")
    assert overall_passed is False
    assert len(results) == 1
    assert "was not generated" in results[0]["message"]

def test_run_command_timeout():
    # We should run a command that takes longer than the timeout
    # e.g., run sleep 2 with a timeout of 0.1s
    exit_code, stdout, stderr = runner.run_command(
        ["sleep", "2"], cwd=".", timeout=0.1
    )
    assert exit_code == -1
    assert "timed out" in stderr


def test_lambda_handler_python_success():
    from unittest.mock import patch
    event = {
        "language": "python",
        "code": "def add(a, b): return a + b",
        "test_suite": "def test_add(): assert add(1, 2) == 3"
    }
    
    mock_response = {
        "stdout": "pytest stdout",
        "stderr": "",
        "passed": True,
        "test_results": [{"name": "test_add", "passed": True, "message": ""}]
    }
    
    with patch("runner.execute_sandbox", return_value=mock_response) as mock_exec:
        # Clear environment variables to ensure they get set
        for k in ["LANGUAGE", "CODE", "TEST_SUITE", "TIMEOUT_LIMIT"]:
            if k in os.environ:
                del os.environ[k]
                
        res = runner.lambda_handler(event, None)
        
        # Verify execute_sandbox was called with the correct arguments
        mock_exec.assert_called_once_with("python", event["code"], event["test_suite"])
        
        # Verify environmental configurations were set
        assert os.environ.get("LANGUAGE") == "python"
        assert os.environ.get("CODE") == event["code"]
        assert os.environ.get("TEST_SUITE") == event["test_suite"]
        
        # Verify the returned dict matches mock response
        assert res == mock_response


def test_lambda_handler_node_success():
    from unittest.mock import patch
    event = {
        "language": "javascript",
        "code": "function add(a, b) { return a + b; }",
        "test_suite": "test('add', () => { assert.equal(add(1, 2), 3); });",
        "timeout": 10
    }
    
    mock_response = {
        "stdout": "node stdout",
        "stderr": "",
        "passed": True,
        "test_results": [{"name": "add", "passed": True, "message": ""}]
    }
    
    with patch("runner.execute_sandbox", return_value=mock_response) as mock_exec:
        for k in ["LANGUAGE", "CODE", "TEST_SUITE", "TIMEOUT_LIMIT"]:
            if k in os.environ:
                del os.environ[k]
                
        res = runner.lambda_handler(event, None)
        
        mock_exec.assert_called_once_with("javascript", event["code"], event["test_suite"])
        assert os.environ.get("LANGUAGE") == "javascript"
        assert os.environ.get("CODE") == event["code"]
        assert os.environ.get("TEST_SUITE") == event["test_suite"]
        assert os.environ.get("TIMEOUT_LIMIT") == "10"
        assert res == mock_response


def test_lambda_handler_unsupported_language():
    event = {
        "language": "rust",
        "code": "fn main() {}",
        "test_suite": ""
    }
    
    res = runner.lambda_handler(event, None)
    assert res["passed"] is False
    assert len(res["test_results"]) == 1
    assert res["test_results"][0]["name"] == "initialization"
    assert "Unsupported language: rust" in res["test_results"][0]["message"]


def test_lambda_handler_environment_leak_prevention():
    from unittest.mock import patch
    
    event1 = {
        "language": "python",
        "code": "def add(a, b): return a + b",
        "test_suite": "def test_add(): assert add(1, 2) == 3",
        "timeout": 10
    }
    
    mock_response = {
        "stdout": "pytest stdout",
        "stderr": "",
        "passed": True,
        "test_results": []
    }
    
    with patch("runner.execute_sandbox", return_value=mock_response):
        runner.lambda_handler(event1, None)
        assert os.environ.get("LANGUAGE") == "python"
        assert os.environ.get("CODE") == event1["code"]
        assert os.environ.get("TEST_SUITE") == event1["test_suite"]
        assert os.environ.get("TIMEOUT_LIMIT") == "10"
        
        event2 = {}
        runner.lambda_handler(event2, None)
        assert os.environ.get("LANGUAGE") == ""
        assert os.environ.get("CODE") == ""
        assert os.environ.get("TEST_SUITE") == ""
        assert "TIMEOUT_LIMIT" not in os.environ


def test_execute_sandbox_stale_report_cleanup():
    from unittest.mock import patch
    
    os.makedirs(runner.SANDBOX_DIR, exist_ok=True)
    report_file = os.path.join(runner.SANDBOX_DIR, "report.json")
    with open(report_file, "w") as f:
        f.write('{"stale": true}')
        
    def mock_rmtree(path, *args, **kwargs):
        raise OSError("Permission denied / directory busy")
        
    with patch("shutil.rmtree", side_effect=mock_rmtree), \
         patch("runner.run_command", return_value=(0, "ok", "")) as mock_run:
         
        runner.execute_sandbox("python", "print('hello')", "")
        
        assert not os.path.exists(report_file)


def test_execute_sandbox_python_success():
    from unittest.mock import patch
    
    # 1. Success case with pytest
    pytest_report = {
        "exitcode": 0,
        "tests": [
            {"nodeid": "test_suite.py::test_one", "outcome": "passed"}
        ]
    }
    
    def mock_run_command(cmd, cwd, timeout):
        # write the pytest json report
        report_file = os.path.join(runner.SANDBOX_DIR, "report.json")
        with open(report_file, "w") as f:
            json.dump(pytest_report, f)
        return 0, "pytest output", ""
        
    with patch("runner.run_command", side_effect=mock_run_command):
        res = runner.execute_sandbox("python", "def solution(): pass", "def test_one(): pass")
        assert res["passed"] is True
        assert res["stdout"] == "pytest output"
        assert len(res["test_results"]) == 1
        assert res["test_results"][0]["name"] == "test_suite.py::test_one"
        assert res["test_results"][0]["passed"] is True


def test_execute_sandbox_python_no_tests_collected():
    from unittest.mock import patch
    
    # Pytest returns exit code 5 (no tests collected).
    # Then it falls back to direct python run.
    call_count = 0
    def mock_run_command(cmd, cwd, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return 5, "no tests collected", ""
        else:
            return 0, "direct script output", ""
            
    with patch("runner.run_command", side_effect=mock_run_command):
        res = runner.execute_sandbox("python", "print(123)", "print(456)")
        assert res["passed"] is True
        assert res["stdout"] == "direct script output"
        assert len(res["test_results"]) == 1
        assert res["test_results"][0]["name"] == "test_suite.py"
        assert res["test_results"][0]["passed"] is True


def test_execute_sandbox_python_timeout():
    from unittest.mock import patch
    
    # run_command returns exit code -1 (timeout)
    with patch("runner.run_command", return_value=(-1, "", "Execution timed out")):
        res = runner.execute_sandbox("python", "while True: pass", "def test_loop(): pass")
        assert res["passed"] is False
        assert len(res["test_results"]) == 1
        assert "timeout" in res["test_results"][0]["name"]
        assert "timed out" in res["test_results"][0]["message"]


def test_execute_sandbox_python_execution_error():
    from unittest.mock import patch
    
    # run_command returns general error code (e.g., 3) and no report file is created
    with patch("runner.run_command", return_value=(3, "", "SyntaxError: invalid syntax")):
        res = runner.execute_sandbox("python", "invalid python", "def test_invalid(): pass")
        assert res["passed"] is False
        assert len(res["test_results"]) == 1
        assert "execution error" in res["test_results"][0]["name"]
        assert "SyntaxError" in res["test_results"][0]["message"]


def test_execute_sandbox_node_success():
    from unittest.mock import patch
    
    # Success case with node test runner
    node_report_lines = [
        json.dumps({"type": "test:pass", "data": {"name": "node test"}})
    ]
    
    def mock_run_command(cmd, cwd, timeout):
        report_file = os.path.join(runner.SANDBOX_DIR, "report.json")
        with open(report_file, "w") as f:
            f.write("\n".join(node_report_lines))
        return 0, "node output", ""
        
    with patch("runner.run_command", side_effect=mock_run_command):
        res = runner.execute_sandbox("node", "const x = 1;", "test('node test', () => {})")
        assert res["passed"] is True
        assert res["stdout"] == "node output"
        assert len(res["test_results"]) == 1
        assert res["test_results"][0]["name"] == "node test"
        assert res["test_results"][0]["passed"] is True


def test_execute_sandbox_node_no_tests_collected():
    from unittest.mock import patch
    
    # Node returns exit code 0 but no tests were run
    with patch("runner.run_command", return_value=(0, "node output", "")) as mock_run:
        res = runner.execute_sandbox("node", "const x = 1;", "")
        assert res["passed"] is True
        assert len(res["test_results"]) == 1
        assert "solution.js" in res["test_results"][0]["name"]


def test_execute_sandbox_node_timeout_with_results():
    from unittest.mock import patch
    
    # Node execution times out (-1) but has generated some test reports
    node_report_lines = [
        json.dumps({"type": "test:pass", "data": {"name": "first test"}})
    ]
    def mock_run_command(cmd, cwd, timeout):
        report_file = os.path.join(runner.SANDBOX_DIR, "report.json")
        with open(report_file, "w") as f:
            f.write("\n".join(node_report_lines))
        return -1, "partial output", "timeout error"
        
    with patch("runner.run_command", side_effect=mock_run_command):
        res = runner.execute_sandbox("javascript", "const x = 1;", "test('first test')")
        assert res["passed"] is False
        assert len(res["test_results"]) == 2
        assert res["test_results"][0]["name"] == "first test"
        assert res["test_results"][0]["passed"] is True
        assert res["test_results"][1]["name"] == "timeout"
        assert res["test_results"][1]["passed"] is False


def test_execute_sandbox_empty_language():
    res = runner.execute_sandbox("", "print(1)", "")
    assert res["passed"] is False
    assert "LANGUAGE environment variable is required" in res["stderr"]


def test_lambda_handler_exception():
    from unittest.mock import patch
    # Cause execute_sandbox to raise an exception
    with patch("runner.execute_sandbox", side_effect=RuntimeError("Unexpected error")):
        res = runner.lambda_handler({"language": "python", "code": "print(1)"}, None)
        assert res["passed"] is False
        assert len(res["test_results"]) == 1
        assert res["test_results"][0]["name"] == "sandbox-lambda handler error"
        assert "Unexpected error" in res["test_results"][0]["message"]


def test_main_success():
    from unittest.mock import patch
    import io
    
    mock_result = {"stdout": "out", "stderr": "err", "passed": True, "test_results": []}
    
    env_mock = {
        "LANGUAGE": "python",
        "CODE": "print(1)",
        "TEST_SUITE": "assert True"
    }
    
    # Redirect stdout to capture print
    captured_stdout = io.StringIO()
    with patch.dict(os.environ, env_mock), \
         patch("runner.execute_sandbox", return_value=mock_result), \
         patch("sys.stdout", new=captured_stdout):
         
        runner.main()
        
    output = json.loads(captured_stdout.getvalue().strip())
    assert output == mock_result


def test_main_empty_language():
    from unittest.mock import patch
    import io
    
    # Redirect stdout to capture print
    captured_stdout = io.StringIO()
    with patch.dict(os.environ, {}, clear=True), \
         patch("sys.stdout", new=captured_stdout):
         
        with pytest.raises(SystemExit):
            runner.main()
        
    output = json.loads(captured_stdout.getvalue().strip())
    assert output["passed"] is False
    assert "LANGUAGE environment variable is required" in output["stderr"]


def test_main_exception():
    from unittest.mock import patch
    import io
    
    env_mock = {
        "LANGUAGE": "python",
        "CODE": "print(1)",
        "TEST_SUITE": "assert True"
    }
    
    # Redirect stdout to capture print
    captured_stdout = io.StringIO()
    with patch.dict(os.environ, env_mock), \
         patch("runner._main_impl", side_effect=RuntimeError("main crash")), \
         patch("sys.stdout", new=captured_stdout):
         
        runner.main()
        
    output = json.loads(captured_stdout.getvalue().strip())
    assert output["passed"] is False
    assert "main crash" in output["test_results"][0]["message"]



