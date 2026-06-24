import os
import sys
import json
import subprocess
import re
import shutil
import time
from typing import Dict, List, Any, Tuple, Optional

# Constants
SANDBOX_DIR = "/tmp/sandbox"
TIMEOUT_LIMIT = 5  # seconds

# Global start time for dynamic timeout tracking
START_TIME: Optional[float] = None

def run_command(cmd: List[str], cwd: str, timeout_limit: float = TIMEOUT_LIMIT) -> Tuple[int, str, str]:
    """Runs a command in a subprocess with dynamic remaining timeout and captures stdout/stderr.
    
    Returns:
        A tuple of (exit_code, stdout, stderr).
    """
    global START_TIME
    if START_TIME is None:
        START_TIME = time.time()
        
    elapsed = time.time() - START_TIME
    remaining = timeout_limit - elapsed
    if remaining <= 0:
        return -1, "", f"Execution timed out after {timeout_limit} seconds."
        
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=remaining,
            errors="replace"
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        # If timed out, return exit code -1 and the stdout/stderr accumulated so far
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        if not stderr:
            stderr = f"Execution timed out after {timeout_limit} seconds."
        return -1, stdout, stderr
    except Exception as e:
        return -2, "", str(e)

def parse_pytest_report(report_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Parses a pytest-json-report file.
    
    Returns:
        A tuple of (overall_passed, test_results).
    """
    test_results: List[Dict[str, Any]] = []
    overall_passed = True
    
    if not os.path.exists(report_path):
        return False, [{"name": "pytest-report", "passed": False, "message": "pytest-json-report was not generated."}]

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Check overall exitcode from the report. If exitcode is not 0, then some test failed
        # or there was a collection/syntax error.
        exitcode = data.get("exitcode", 0)
        if exitcode != 0:
            overall_passed = False
            
        # Check collectors for errors (e.g., collection/syntax errors)
        collectors = data.get("collectors", [])
        for c in collectors:
            if c.get("outcome") == "failed":
                overall_passed = False
                test_results.append({
                    "name": f"collection::{c.get('nodeid', 'unknown')}",
                    "passed": False,
                    "message": c.get("longrepr", "Collection failed")
                })
                
        # Check actual test results
        tests = data.get("tests", [])
        for t in tests:
            nodeid: str = t.get("nodeid", "")
            outcome: str = t.get("outcome", "")
            msg = ""
            
            # If failed/error, extract the crash message
            if outcome != "passed":
                overall_passed = False
                call_info = t.get("call", {})
                setup_info = t.get("setup", {})
                teardown_info = t.get("teardown", {})
                
                # Check call phase crash message first, then setup, then teardown
                crash = call_info.get("crash", {}) or setup_info.get("crash", {}) or teardown_info.get("crash", {})
                msg = crash.get("message", "") if crash else ""
                
                if not msg:
                    # Fallback to longrepr if message is not in crash
                    msg = t.get("call", {}).get("longrepr", "") or t.get("setup", {}).get("longrepr", "")
                    
            test_results.append({
                "name": nodeid,
                "passed": outcome == "passed",
                "message": msg
            })
            
    except Exception as e:
        overall_passed = False
        test_results.append({
            "name": "pytest-report-parser",
            "passed": False,
            "message": f"Error parsing report: {e}"
        })
        
    return overall_passed, test_results

def detect_esm(code: str) -> bool:
    """Uses a regex to check for top-level import/export statements to detect ES Modules."""
    esm_pattern = re.compile(
        r"^\s*(?:import\s+(?:[\w*$\s,{}]+from\s+)?['\"]|import\s*\(|import\s+['\"]|export\s+(?:default|const|let|var|class|function|async|\{))",
        re.MULTILINE
    )
    return bool(esm_pattern.search(code))

def format_node_error(error_info: Dict[str, Any]) -> str:
    """Formats Node.js test runner error details into a readable string."""
    if not isinstance(error_info, dict):
        return str(error_info) if error_info else "Test failed"
    
    message = error_info.get("message", "")
    if message:
        return message
        
    cause = error_info.get("cause")
    if isinstance(cause, dict):
        cause_msg = cause.get("message", "")
        if cause_msg:
            return cause_msg
            
        code = cause.get("code")
        if code == "ERR_ASSERTION" or "operator" in cause:
            actual = cause.get("actual")
            expected = cause.get("expected")
            operator = cause.get("operator")
            return f"AssertionError: Expected {expected} {operator} {actual} (failed)"
        return str(cause)
    elif cause:
        return str(cause)
        
    failure_type = error_info.get("failureType")
    code = error_info.get("code")
    if failure_type or code:
        return f"{code or 'Error'}: {failure_type or 'Unknown failure'}"
        
    stack = error_info.get("stack", "")
    if stack:
        return stack
        
    return str(error_info)

def parse_node_json_report(report_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Parses a Node.js JSON reporter output file.
    
    Each line is a JSON object. We are interested in `test:fail` and `test:pass` event types,
    as well as `test:stderr` diagnostics.
    Extracts the test `name`, `passed` status, and any error message details.
    
    Returns:
        A tuple of (overall_passed, test_results).
    """
    test_results: List[Dict[str, Any]] = []
    overall_passed = True
    
    if not os.path.exists(report_path):
        return False, []
        
    stderr_messages: List[str] = []
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                event_type = event.get("type")
                data = event.get("data", {})
                if not isinstance(data, dict):
                    continue
                    
                if event_type == "test:stderr":
                    msg = data.get("message", "")
                    if msg:
                        stderr_messages.append(msg)
                elif event_type in ("test:pass", "test:fail"):
                    name = data.get("name", "unknown")
                    passed = (event_type == "test:pass")
                    
                    message = ""
                    if not passed:
                        overall_passed = False
                        # Extract error details
                        details = data.get("details", {})
                        error_info = {}
                        if isinstance(details, dict):
                            error_info = details.get("error", {})
                        if not error_info or not isinstance(error_info, dict):
                            error_info = data.get("error", {})
                        
                        message = format_node_error(error_info)
                        
                        if stderr_messages:
                            stderr_str = "".join(stderr_messages).strip()
                            if stderr_str:
                                if message:
                                    message = f"{message}\n\nConsole Stderr:\n{stderr_str}"
                                else:
                                    message = stderr_str
                                    
                    test_results.append({
                        "name": name,
                        "passed": passed,
                        "message": message
                    })
                    stderr_messages = []
    except Exception as e:
        overall_passed = False
        test_results.append({
            "name": "node-report-parser",
            "passed": False,
            "message": f"Error parsing report: {e}"
        })
        
    return overall_passed, test_results

def main() -> None:
    global START_TIME
    START_TIME = time.time()

    # Set default values
    stdout = ""
    stderr = ""
    passed = False
    test_results: List[Dict[str, Any]] = []
    
    # Clean and recreate sandbox directory
    if os.path.exists(SANDBOX_DIR):
        shutil.rmtree(SANDBOX_DIR)
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    
    # Read environment variables
    language = os.environ.get("LANGUAGE", "").lower().strip()
    code = os.environ.get("CODE", "")
    test_suite = os.environ.get("TEST_SUITE", "")
    
    if not language:
        stderr = "Error: LANGUAGE environment variable is required."
        print(json.dumps({
            "stdout": stdout,
            "stderr": stderr,
            "passed": passed,
            "test_results": test_results
        }))
        sys.exit(0)
        
    if language in ["python", "py"]:
        solution_file = os.path.join(SANDBOX_DIR, "solution.py")
        test_file = os.path.join(SANDBOX_DIR, "test_suite.py")
        
        # Write user code
        with open(solution_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        if test_suite:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_suite)
                
            # Run pytest with json report
            report_file = os.path.join(SANDBOX_DIR, "report.json")
            cmd = [
                "pytest",
                "--json-report",
                f"--json-report-file={report_file}",
                test_file
            ]
            exit_code, stdout, stderr = run_command(cmd, SANDBOX_DIR)
            
            # Pytest exit code 5 means no tests were collected.
            # In that case, we fall back to running the test suite as a direct python script.
            if exit_code == 5:
                # Fallback to direct python run
                exit_code, stdout, stderr = run_command(["python3", test_file], SANDBOX_DIR)
                passed = (exit_code == 0)
                test_results = [{
                    "name": "test_suite.py",
                    "passed": passed,
                    "message": stderr if not passed else ""
                }]
            elif exit_code in [0, 1, 2]:
                # 0 = all passed, 1 = some failed, 2 = collection error
                passed, test_results = parse_pytest_report(report_file)
            elif exit_code == -1:
                # Timeout
                passed = False
                test_results = [{
                    "name": "timeout",
                    "passed": False,
                    "message": f"Execution timed out (limit: {TIMEOUT_LIMIT}s)"
                }]
            else:
                # Other execution error (syntax errors, import errors, etc.)
                passed = False
                # If report.json exists, try parsing it because syntax error might be recorded there
                if os.path.exists(report_file):
                    passed, test_results = parse_pytest_report(report_file)
                else:
                    test_results = [{
                        "name": "test_suite.py (execution error)",
                        "passed": False,
                        "message": stderr
                    }]
        else:
            # No test suite, run solution.py directly
            exit_code, stdout, stderr = run_command(["python3", solution_file], SANDBOX_DIR)
            passed = (exit_code == 0)
            test_results = [{
                "name": "solution.py",
                "passed": passed,
                "message": stderr if not passed else ""
            }]
            
    elif language in ["javascript", "js", "node"]:
        solution_file = os.path.join(SANDBOX_DIR, "solution.js")
        test_file = os.path.join(SANDBOX_DIR, "test_suite.js")
        
        # Write user code
        with open(solution_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Detect if we should use ESM or CommonJS
        is_esm = detect_esm(code) or detect_esm(test_suite)
        if is_esm:
            package_json = os.path.join(SANDBOX_DIR, "package.json")
            with open(package_json, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "module"}))
                
        if test_suite:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_suite)
                
            # Run node test runner with JSON reporter
            report_file = os.path.join(SANDBOX_DIR, "report.json")
            cmd = [
                "node",
                "--test",
                "--test-reporter=json",
                f"--test-reporter-destination={report_file}",
                test_file
            ]
            exit_code, stdout, stderr = run_command(cmd, SANDBOX_DIR)
            
            # Parse JSON report output
            passed, test_results = parse_node_json_report(report_file)
            
            # If no tests were run (empty test_results) and exit_code is non-zero,
            # or if it was a timeout / execution error, report it
            if not test_results:
                passed = (exit_code == 0)
                msg = stderr if stderr else stdout
                if exit_code == -1:
                    msg = f"Execution timed out (limit: {TIMEOUT_LIMIT}s)"
                test_results = [{
                    "name": "test_suite.js (execution error)",
                    "passed": passed,
                    "message": msg
                }]
            elif exit_code == -1:
                # If it was a timeout but some JSON output was generated
                passed = False
                test_results.append({
                    "name": "timeout",
                    "passed": False,
                    "message": f"Execution timed out (limit: {TIMEOUT_LIMIT}s)"
                })
        else:
            # No test suite, run solution.js directly
            exit_code, stdout, stderr = run_command(["node", solution_file], SANDBOX_DIR)
            passed = (exit_code == 0)
            test_results = [{
                "name": "solution.js",
                "passed": passed,
                "message": stderr if not passed else ""
            }]
    else:
        stderr = f"Unsupported language: {language}"
        passed = False
        test_results = [{
            "name": "initialization",
            "passed": False,
            "message": stderr
        }]
        
    # Print exactly the final JSON output to stdout
    print(json.dumps({
        "stdout": stdout,
        "stderr": stderr,
        "passed": passed,
        "test_results": test_results
    }))

if __name__ == "__main__":
    main()
