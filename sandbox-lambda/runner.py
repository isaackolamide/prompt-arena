import os
import sys
import json
import subprocess
import re
import shutil
from typing import Dict, List, Any, Tuple, Optional

# Constants
SANDBOX_DIR = "/tmp/sandbox"
TIMEOUT_LIMIT = 5  # seconds

def run_command(cmd: List[str], cwd: str, timeout: int = TIMEOUT_LIMIT) -> Tuple[int, str, str]:
    """Runs a command in a subprocess with a timeout and captures stdout/stderr.
    
    Returns:
        A tuple of (exit_code, stdout, stderr).
    """
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        # If timed out, return exit code -1 and the stdout/stderr accumulated so far
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        if not stderr:
            stderr = f"Execution timed out after {timeout} seconds."
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

def parse_tap_output(tap_text: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Parses TAP format output from node test runner, capturing preceding comments.
    
    Returns:
        A tuple of (overall_passed, test_results).
    """
    test_results: List[Dict[str, Any]] = []
    overall_passed = True
    
    lines = tap_text.splitlines()
    recent_comments: List[str] = []
    current_test: Optional[Dict[str, Any]] = None
    
    for line in lines:
        line_strip = line.strip()
        
        # Match lines like "ok 1 - test description" or "not ok 2 - test description"
        m = re.match(r'^(not\s+)?ok\s+\d+\s+-\s+(.+)$', line_strip)
        if m:
            is_not_ok = bool(m.group(1))
            name = m.group(2).strip()
            
            # Include preceding comments if the test failed
            msg = ""
            if is_not_ok and recent_comments:
                msg = "\n".join(recent_comments)
                
            current_test = {
                "name": name,
                "passed": not is_not_ok,
                "message": msg
            }
            test_results.append(current_test)
            if is_not_ok:
                overall_passed = False
            # Clear comments for next test
            recent_comments = []
        elif line_strip.startswith('#'):
            # Collect comment lines
            comment = line_strip[1:].strip()
            if comment:
                recent_comments.append(comment)
        elif current_test is not None:
            # Accumulate failure details/yaml diagnostics for the current failed test
            if line_strip.startswith('---') or line_strip.startswith('...'):
                continue
            
            # If we are in yaml blocks, capture fields like "error:" or "stack:" or standard messages
            if current_test["passed"] is False:
                # Append relevant diagnostic lines
                if current_test["message"]:
                    current_test["message"] += "\n" + line_strip
                else:
                    current_test["message"] = line_strip
                    
    # Clean up test messages
    for t in test_results:
        if t["message"]:
            t["message"] = t["message"].strip()
            
    return overall_passed, test_results

def main() -> None:
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
                    "message": "Execution timed out (limit: 5s)"
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
        is_esm = ("import " in code or "export " in code or 
                  "import " in test_suite or "export " in test_suite)
        if is_esm:
            package_json = os.path.join(SANDBOX_DIR, "package.json")
            with open(package_json, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "module"}))
                
        if test_suite:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_suite)
                
            # Run node test runner with tap output
            cmd = ["node", "--test", "--test-reporter=tap", test_file]
            exit_code, stdout, stderr = run_command(cmd, SANDBOX_DIR)
            
            # Parse TAP output from stdout
            passed, test_results = parse_tap_output(stdout)
            
            # If no tests were run (empty test_results) and exit_code is non-zero,
            # or if it was a timeout / execution error, report it
            if not test_results:
                passed = (exit_code == 0)
                msg = stderr if stderr else stdout
                if exit_code == -1:
                    msg = "Execution timed out (limit: 5s)"
                test_results = [{
                    "name": "test_suite.js (execution error)",
                    "passed": passed,
                    "message": msg
                }]
            elif exit_code == -1:
                # If it was a timeout but some TAP output was generated
                passed = False
                test_results.append({
                    "name": "timeout",
                    "passed": False,
                    "message": "Execution timed out (limit: 5s)"
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
