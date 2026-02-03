"""HumanEval benchmark loader and execution harness."""

import gzip
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


DATASET_FILES = {
    "humaneval": "HumanEval.jsonl",
    "humaneval+": "HumanEvalPlus-OriginFmt.jsonl",
}


class HumanEval:
    """Loader for HumanEval benchmark problems."""

    def __init__(self, data_path: Optional[str] = None, dataset: str = "humaneval"):
        """Initialize HumanEval loader.

        Args:
            data_path: Path to dataset JSONL file. When None, resolves from dataset name.
            dataset: Dataset name ("humaneval" or "humaneval+"). Ignored when data_path is provided.
        """
        if data_path is None:
            dataset_lower = dataset.lower()
            if dataset_lower not in DATASET_FILES:
                raise ValueError(
                    f"Unknown dataset '{dataset}'. Choose from: {', '.join(DATASET_FILES.keys())}"
                )
            package_dir = Path(__file__).parent.parent
            data_path = package_dir / "data" / DATASET_FILES[dataset_lower]

        self.data_path = Path(data_path)
        self.dataset = dataset.lower()
        self.problems = self._load_problems()

    def _load_problems(self) -> dict:
        """Load problems from JSONL file (plain or gzipped).

        Returns:
            Dictionary mapping task_id to problem dict
        """
        problems = {}

        path = self.data_path
        gz_path = Path(str(self.data_path) + ".gz")

        if path.exists():
            opener = open
        elif gz_path.exists():
            opener = gzip.open
            path = gz_path
        else:
            return problems

        with opener(path, 'rt') as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    problems[item["task_id"]] = item

        return problems

    def get_problem(self, task_id: str) -> dict:
        """Get a specific problem by ID.

        Args:
            task_id: Problem ID (e.g., "HumanEval/0")

        Returns:
            Problem dictionary

        Raises:
            KeyError: If problem ID not found
        """
        return self.problems[task_id]

    def list_problems(self) -> list[str]:
        """List all available problem IDs.

        Returns:
            List of task IDs
        """
        return list(self.problems.keys())

    def count(self) -> int:
        """Count total problems.

        Returns:
            Number of problems
        """
        return len(self.problems)


def count_test_assertions(test_code: str) -> int:
    """Count the number of assert statements in test code.

    Args:
        test_code: Test code containing assertions

    Returns:
        Number of assert statements found
    """
    # Match assert statements (handle multiline)
    # Pattern: assert ... (can span multiple lines until end of statement)
    assert_pattern = r'^\s*assert\s+.+$'
    matches = re.findall(assert_pattern, test_code, re.MULTILINE)
    return len(matches)


def parse_test_results(code: str, test_code: str, stderr: str, success: bool, total_tests: int) -> int:
    """Determine how many tests passed based on execution results.

    Args:
        code: Solution code
        test_code: Test code
        stderr: Standard error output
        success: Whether execution succeeded
        total_tests: Total number of assertions

    Returns:
        Number of tests that passed
    """
    # If successful, all tests passed
    if success:
        return total_tests

    # If no tests were counted, return 0
    if total_tests == 0:
        return 0

    # Check error type
    if "AssertionError" in stderr:
        # Assertion failed - try to determine which one
        # Look for line number in traceback
        # Example: File "/tmp/xyz.py", line 25, in check
        match = re.search(r'File ".*?", line (\d+), in check', stderr)
        if match:
            error_line = int(match.group(1))

            # Count assertions in test code that come before this line
            # Split code into lines and find line numbers of assertions
            full_code = code + "\n\n" + test_code
            code_lines = full_code.split('\n')

            # Find where test code starts
            code_line_count = len(code.split('\n'))
            test_start_line = code_line_count + 2  # +2 for blank lines

            # Count assertions before the error line
            passed = 0
            for i, line in enumerate(test_code.split('\n')):
                current_line = test_start_line + i
                if current_line >= error_line:
                    break
                if line.strip().startswith('assert '):
                    passed += 1

            return passed

        # Couldn't parse line number, assume first assertion failed
        return 0

    else:
        # Syntax error, name error, import error, etc.
        # No tests actually ran
        return 0


def execute_solution(code: str, test: str, entry_point: str = "", timeout: int = 10) -> dict:
    """Execute a code solution against tests.

    Args:
        code: Python code to execute
        test: Test code (assertions)
        entry_point: Function name to pass to check(). When provided, appends
            ``check(<entry_point>)`` so that test assertions actually execute.
        timeout: Timeout in seconds (default 10 for HumanEval+ compatibility)

    Returns:
        Dictionary with:
            - success (bool): Whether all tests passed
            - tests_passed (int): Number of test assertions that passed
            - tests_total (int): Total number of test assertions
            - test_pass_rate (float): Percentage of tests passed (0.0 to 1.0)
            - stdout (str): Standard output
            - stderr (str): Standard error
            - error (str): Error message if failed
    """
    # Count total test assertions
    total_tests = count_test_assertions(test)

    # Create temporary file with solution + tests
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.write("\n\n")
        f.write(test)
        if entry_point:
            f.write(f"\ncheck({entry_point})\n")
        temp_path = f.name

    try:
        # Run with timeout
        result = subprocess.run(
            [sys.executable, temp_path],
            timeout=timeout,
            capture_output=True,
            text=True
        )

        success = result.returncode == 0

        # Calculate test metrics
        tests_passed = parse_test_results(
            code=code,
            test_code=test,
            stderr=result.stderr,
            success=success,
            total_tests=total_tests
        )

        test_pass_rate = tests_passed / total_tests if total_tests > 0 else 0.0

        return {
            "success": success,
            "tests_passed": tests_passed,
            "tests_total": total_tests,
            "test_pass_rate": test_pass_rate,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": None if success else result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "tests_passed": 0,
            "tests_total": total_tests,
            "test_pass_rate": 0.0,
            "stdout": "",
            "stderr": "",
            "error": f"Timeout after {timeout} seconds"
        }

    except Exception as e:
        return {
            "success": False,
            "tests_passed": 0,
            "tests_total": total_tests,
            "test_pass_rate": 0.0,
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def _extract_prompt_prefix(prompt: str, entry_point: str) -> str:
    """Extract code from the prompt that precedes the entry_point function.

    Many HumanEval problems define helper functions (e.g. ``encode_cyclic``)
    before the target function (``decode_cyclic``).  The tests depend on those
    helpers, so they must be included in the execution context.

    Args:
        prompt: Full HumanEval problem prompt.
        entry_point: Name of the target function.

    Returns:
        All prompt lines before the ``def entry_point(`` line, or empty string
        if entry_point is not found or appears first.
    """
    if not entry_point:
        return ""

    pattern = re.compile(rf'^def\s+{re.escape(entry_point)}\s*\(')
    lines = prompt.split("\n")
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = "\n".join(lines[:i])
            return prefix

    return ""


def verify_solution(problem: dict, solution: str, timeout: int = 10) -> dict:
    """Verify a solution against a problem's tests.

    Args:
        problem: HumanEval problem dictionary
        solution: Python code solution
        timeout: Timeout in seconds for test execution

    Returns:
        Execution result dictionary
    """
    prompt = problem.get("prompt", "")
    entry_point = problem.get("entry_point", "")

    # Prepend helper code from the prompt (functions/imports before entry_point).
    # Tests for multi-function problems call helpers defined in the prompt
    # (e.g. encode_cyclic for HumanEval/38) that the model may not reproduce.
    prefix = _extract_prompt_prefix(prompt, entry_point)
    if prefix.strip():
        full_code = prefix.rstrip() + "\n\n\n" + solution
    else:
        full_code = solution

    test_code = problem.get("test", "")

    return execute_solution(full_code, test_code, entry_point=entry_point, timeout=timeout)
