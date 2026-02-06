"""BigCodeBench benchmark loader and execution harness.

BigCodeBench contains 1,140 coding tasks focused on multi-step reasoning and library
usage. The Hard subset (148 tasks) contains the most challenging problems.

Key differences from HumanEval:
- Uses unittest.TestCase for testing instead of check(candidate) functions
- Requires external libraries (pandas, numpy, matplotlib, etc.)
- Has both complete_prompt (docstring) and instruct_prompt (NL) formats
- Tasks may perform file I/O and require temp directory isolation
"""

import gzip
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


DATASET_FILES = {
    "bigcodebench": "bigcodebench.jsonl",
    "bigcodebench-hard": "bigcodebench_hard.jsonl",
}


class BigCodeBench:
    """Loader for BigCodeBench benchmark problems."""

    def __init__(self, data_path: Optional[str] = None, dataset: str = "bigcodebench-hard"):
        """Initialize BigCodeBench loader.

        Args:
            data_path: Path to dataset JSONL file. When None, resolves from dataset name.
            dataset: Dataset name ("bigcodebench" or "bigcodebench-hard").
                     Ignored when data_path is provided.
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
            task_id: Problem ID (e.g., "BigCodeBench/0")

        Returns:
            Problem dictionary with fields:
                - task_id: Problem ID
                - complete_prompt: Docstring-style prompt
                - instruct_prompt: Natural language prompt
                - entry_point: Function name to implement
                - test: unittest.TestCase test class
                - canonical_solution: Reference solution
                - libs: List of required libraries

        Raises:
            KeyError: If problem ID not found
        """
        return self.problems[task_id]

    def get_prompt(self, task_id: str, mode: str = "complete") -> str:
        """Get prompt for a task.

        Args:
            task_id: Problem ID
            mode: "complete" (docstring-based, default) or "instruct" (NL-based)

        Returns:
            Prompt string for the task
        """
        problem = self.get_problem(task_id)
        if mode == "instruct":
            return problem.get("instruct_prompt", problem.get("complete_prompt", ""))
        return problem.get("complete_prompt", problem.get("prompt", ""))

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


def parse_unittest_output(stderr: str) -> tuple[int, int, list[str]]:
    """Parse unittest verbose output to extract test results.

    Args:
        stderr: Standard error output from unittest run

    Returns:
        Tuple of (tests_passed, tests_total, failure_messages)
    """
    # Pattern for unittest summary line: "Ran X test(s) in Y.YYYs"
    ran_pattern = re.search(r'Ran (\d+) tests? in', stderr)
    tests_total = int(ran_pattern.group(1)) if ran_pattern else 0

    # Count failures and errors
    # Look for "FAILED (failures=X)" or "FAILED (errors=X)" or "FAILED (failures=X, errors=Y)"
    failures = 0
    errors = 0

    fail_pattern = re.search(r'failures=(\d+)', stderr)
    if fail_pattern:
        failures = int(fail_pattern.group(1))

    error_pattern = re.search(r'errors=(\d+)', stderr)
    if error_pattern:
        errors = int(error_pattern.group(1))

    tests_passed = max(0, tests_total - failures - errors)

    # Extract failure messages
    failure_messages = []
    # Pattern matches FAIL: test_name (module.TestClass)
    fail_blocks = re.findall(
        r'(FAIL|ERROR): (test_\w+).*?\n-+\n(.*?)(?=\n[A-Z]+:|$)',
        stderr,
        re.DOTALL
    )
    for fail_type, test_name, message in fail_blocks:
        # Truncate long messages
        short_msg = message.strip()[:500]
        failure_messages.append(f"{fail_type}: {test_name}\n{short_msg}")

    return tests_passed, tests_total, failure_messages


def execute_bigcodebench_solution(
    code: str,
    test: str,
    entry_point: str = "",
    timeout: int = 30,
    libs: Optional[list[str]] = None,
) -> dict:
    """Execute BigCodeBench solution with unittest-based tests.

    BigCodeBench uses unittest.TestCase classes instead of HumanEval's
    check(candidate) pattern. This function handles:
    - Combining solution code with test class
    - Running via subprocess with unittest discovery
    - Parsing unittest output to extract pass/fail counts
    - Temp directory isolation for file-based tests

    Args:
        code: Python code solution to test
        test: unittest.TestCase test class code
        entry_point: Function name being tested (for reference)
        timeout: Timeout in seconds (default 30 - BCB tasks are more complex)
        libs: List of required libraries (for documentation, not enforced)

    Returns:
        Dictionary with:
            - success (bool): Whether all tests passed
            - tests_passed (int): Number of test methods that passed
            - tests_total (int): Total number of test methods
            - test_pass_rate (float): Percentage of tests passed (0.0 to 1.0)
            - stdout (str): Standard output
            - stderr (str): Standard error
            - error (str): Error message if failed
    """
    # Create temporary directory for test isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write combined solution + test file
        test_file = Path(tmpdir) / "test_solution.py"

        # Build test file content
        # Add common imports that BCB tasks typically need
        file_content = '''"""Auto-generated test file for BigCodeBench solution."""
import unittest
import sys
import os
import warnings

# Suppress warnings that might clutter output
warnings.filterwarnings('ignore')

# Change to temp directory for file operations
os.chdir(os.path.dirname(os.path.abspath(__file__)))

'''
        # Add solution code
        file_content += "# Solution code\n"
        file_content += code
        file_content += "\n\n"

        # Add test code
        file_content += "# Test code\n"
        file_content += test
        file_content += "\n\n"

        # Add test runner
        file_content += '''
if __name__ == '__main__':
    unittest.main(verbosity=2)
'''

        test_file.write_text(file_content)

        try:
            # Run unittest in the temp directory
            result = subprocess.run(
                [sys.executable, str(test_file)],
                timeout=timeout,
                capture_output=True,
                text=True,
                cwd=tmpdir,  # Isolate file operations
                env={
                    **dict(os.environ),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )

            # Parse unittest output
            tests_passed, tests_total, failure_messages = parse_unittest_output(result.stderr)

            # Determine success
            success = result.returncode == 0 and tests_total > 0

            # Calculate pass rate
            test_pass_rate = tests_passed / tests_total if tests_total > 0 else 0.0

            # Build error message if failed
            error = None
            if not success:
                if tests_total == 0:
                    error = "No tests found or tests failed to run"
                elif failure_messages:
                    error = "\n---\n".join(failure_messages[:3])  # First 3 failures
                else:
                    # Extract error from stderr
                    error = result.stderr[-1000:] if result.stderr else "Unknown error"

            return {
                "success": success,
                "tests_passed": tests_passed,
                "tests_total": tests_total,
                "test_pass_rate": test_pass_rate,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": error,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_total": 0,
                "test_pass_rate": 0.0,
                "stdout": "",
                "stderr": "",
                "error": f"Timeout after {timeout} seconds",
            }

        except Exception as e:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_total": 0,
                "test_pass_rate": 0.0,
                "stdout": "",
                "stderr": "",
                "error": str(e),
            }


def verify_bigcodebench_solution(
    problem: dict,
    solution: str,
    timeout: int = 30,
    prompt_mode: str = "complete"
) -> dict:
    """Verify a solution against a BigCodeBench problem's tests.

    Args:
        problem: BigCodeBench problem dictionary
        solution: Python code solution
        timeout: Timeout in seconds for test execution
        prompt_mode: Which prompt was used ("complete" or "instruct")

    Returns:
        Execution result dictionary
    """
    test_code = problem.get("test", "")
    entry_point = problem.get("entry_point", "")
    libs = problem.get("libs", [])

    return execute_bigcodebench_solution(
        code=solution,
        test=test_code,
        entry_point=entry_point,
        timeout=timeout,
        libs=libs,
    )


# Import os for env operations in execute function
import os
