import os
import sys
import json
import time

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
    # Set starting time
    runner.START_TIME = time.time()
    
    # We should run a command that takes longer than the remaining timeout
    # e.g., run sleep 2 with dynamic remaining timeout of 0.1s
    exit_code, stdout, stderr = runner.run_command(["sleep", "2"], cwd=".", timeout_limit=0.1)
    assert exit_code == -1
    assert "timed out" in stderr
