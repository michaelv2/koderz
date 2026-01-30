"""HumanEval benchmark loader and execution harness."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class HumanEval:
    """Loader for HumanEval benchmark problems."""

    def __init__(self, data_path: Optional[str] = None):
        """Initialize HumanEval loader.

        Args:
            data_path: Path to HumanEval.jsonl file
        """
        if data_path is None:
            # Default to data/ directory in package
            package_dir = Path(__file__).parent.parent
            data_path = package_dir / "data" / "HumanEval.jsonl"

        self.data_path = Path(data_path)
        self.problems = self._load_problems()

    def _load_problems(self) -> dict:
        """Load problems from JSONL file.

        Returns:
            Dictionary mapping task_id to problem dict
        """
        problems = {}

        if not self.data_path.exists():
            # Return empty dict if file doesn't exist yet
            return problems

        with open(self.data_path) as f:
            for line in f:
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


def execute_solution(code: str, test: str, timeout: int = 5) -> dict:
    """Execute a code solution against tests.

    Args:
        code: Python code to execute
        test: Test code (assertions)
        timeout: Timeout in seconds

    Returns:
        Dictionary with:
            - success (bool): Whether all tests passed
            - stdout (str): Standard output
            - stderr (str): Standard error
            - error (str): Error message if failed
    """
    # Create temporary file with solution + tests
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.write("\n\n")
        f.write(test)
        temp_path = f.name

    try:
        # Run with timeout
        result = subprocess.run(
            ["python3", temp_path],
            timeout=timeout,
            capture_output=True,
            text=True
        )

        success = result.returncode == 0

        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": None if success else result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"Timeout after {timeout} seconds"
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def verify_solution(problem: dict, solution: str) -> dict:
    """Verify a solution against a problem's tests.

    Args:
        problem: HumanEval problem dictionary
        solution: Python code solution

    Returns:
        Execution result dictionary
    """
    # Combine solution with test code
    full_code = solution
    test_code = problem.get("test", "")

    return execute_solution(full_code, test_code)
