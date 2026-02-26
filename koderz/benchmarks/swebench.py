"""SWE-bench benchmark loader and evaluation harness.

SWE-bench contains real-world GitHub issue resolution tasks. The model receives
an issue description and file contents, then generates modified files.

Key differences from HumanEval/BigCodeBench:
- Multi-file output (complete modified files, not function bodies)
- Evaluation requires a real git repo + running its test suite
- Uses git worktrees for isolated per-instance evaluation
- Two test categories: FAIL_TO_PASS (must fix) and PASS_TO_PASS (must not break)

Known limitations (MVP):
- Oracle context only: shows files from the gold patch (not retrieval)
- No Docker: tests run in host Python env
- Best-effort dependency installation
"""

import gzip
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .repo_manager import ensure_repo_clone, worktree_context, read_file_at_commit
from ..utils.multi_file_extraction import extract_files_from_response


DATASET_FILES = {
    "swebench-verified": "swebench_verified.jsonl",
    "swebench-lite": "swebench_lite.jsonl",
}


class SWEBench:
    """Loader for SWE-bench benchmark instances."""

    def __init__(
        self,
        data_path: Optional[str] = None,
        dataset: str = "swebench-verified",
        repo_cache_dir: Optional[str] = None,
    ):
        """Initialize SWE-bench loader.

        Args:
            data_path: Path to dataset JSONL file. When None, resolves from dataset name.
            dataset: Dataset name ("swebench-verified" or "swebench-lite").
            repo_cache_dir: Directory for cached git repos. Defaults to ~/.koderz/swebench-repos.
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
        self.repo_cache_dir = repo_cache_dir
        self.problems = self._load_problems()

    def _load_problems(self) -> dict:
        """Load instances from JSONL file (plain or gzipped).

        Returns:
            Dictionary mapping instance_id to instance dict
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

        with opener(path, "rt") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    # SWE-bench uses instance_id as the primary key
                    instance_id = item.get("instance_id", item.get("task_id", ""))
                    item["task_id"] = instance_id  # Normalize for koderz compatibility
                    problems[instance_id] = item

        return problems

    def get_problem(self, task_id: str) -> dict:
        """Get a specific instance by ID.

        Args:
            task_id: Instance ID (e.g., "django__django-16379")

        Returns:
            Instance dictionary

        Raises:
            KeyError: If instance ID not found
        """
        return self.problems[task_id]

    def list_problems(self) -> list[str]:
        """List all available instance IDs.

        Returns:
            List of instance IDs
        """
        return list(self.problems.keys())

    def count(self) -> int:
        """Count total instances.

        Returns:
            Number of instances
        """
        return len(self.problems)

    def get_oracle_context(self, instance: dict) -> dict[str, str]:
        """Get file contents for the files touched by the gold patch.

        This is "oracle" context — it tells the model exactly which files to modify.

        Args:
            instance: SWE-bench instance dictionary

        Returns:
            Dict mapping filepath -> file contents at base_commit
        """
        patch = instance.get("patch", "")
        repo = instance.get("repo", "")
        base_commit = instance.get("base_commit", "")

        if not patch or not repo or not base_commit:
            return {}

        filepaths = parse_patch_files(patch)
        repo_dir = ensure_repo_clone(repo, cache_dir=self.repo_cache_dir or os.path.expanduser("~/.koderz/swebench-repos"))

        context = {}
        for fp in filepaths:
            try:
                content = read_file_at_commit(repo_dir, base_commit, fp)
                context[fp] = content
            except subprocess.CalledProcessError:
                # File may not exist at that commit (newly created file)
                context[fp] = ""

        return context

    def get_prompt(self, task_id: str) -> str:
        """Get the problem statement for an instance.

        Args:
            task_id: Instance ID

        Returns:
            Problem statement string
        """
        instance = self.get_problem(task_id)
        return instance.get("problem_statement", "")


def parse_patch_files(patch: str) -> list[str]:
    """Extract file paths from a unified diff.

    Parses ``diff --git a/... b/...`` lines to get the list of files
    modified by the patch.

    Args:
        patch: Unified diff string

    Returns:
        Deduplicated list of file paths
    """
    paths = []
    seen = set()
    for line in patch.split("\n"):
        match = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
        if match:
            # Use b/ path (the destination, handles renames)
            filepath = match.group(2)
            if filepath not in seen:
                paths.append(filepath)
                seen.add(filepath)
    return paths


def extract_modified_files(response: str) -> list[dict]:
    """Extract modified files from a model response.

    Delegates to the shared multi-file extraction utility.

    Args:
        response: Raw model response text

    Returns:
        List of {"path": "...", "code": "..."} dicts
    """
    return extract_files_from_response(response)


def apply_modifications(worktree_dir: str, modifications: list[dict]) -> list[str]:
    """Write modified files into a worktree.

    Args:
        worktree_dir: Path to the git worktree
        modifications: List of {"path": "...", "code": "..."} dicts

    Returns:
        List of file paths that were written
    """
    written = []
    for mod in modifications:
        filepath = os.path.join(worktree_dir, mod["path"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(mod["code"])
        written.append(mod["path"])
    return written


def generate_patch(worktree_dir: str) -> str:
    """Generate a unified diff from the worktree's uncommitted changes.

    Args:
        worktree_dir: Path to the git worktree

    Returns:
        Unified diff string
    """
    result = subprocess.run(
        ["git", "diff"],
        cwd=worktree_dir,
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_pytest_output(stdout: str, stderr: str) -> tuple[int, int, list[str]]:
    """Parse pytest output to extract pass/fail counts.

    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest

    Returns:
        Tuple of (tests_passed, tests_total, failure_messages)
    """
    combined = stdout + "\n" + stderr

    passed = 0
    failed = 0
    errors = 0

    # Parse pytest summary line: "X passed, Y failed, Z error"
    pass_match = re.search(r"(\d+) passed", combined)
    if pass_match:
        passed = int(pass_match.group(1))

    fail_match = re.search(r"(\d+) failed", combined)
    if fail_match:
        failed = int(fail_match.group(1))

    error_match = re.search(r"(\d+) error", combined)
    if error_match:
        errors = int(error_match.group(1))

    tests_total = passed + failed + errors
    tests_passed = passed

    # Extract failure messages
    failure_messages = []
    fail_blocks = re.findall(
        r"(FAILED|ERROR)\s+(.+?)(?:\n|$)",
        combined,
    )
    for fail_type, test_name in fail_blocks:
        failure_messages.append(f"{fail_type}: {test_name.strip()}")

    return tests_passed, tests_total, failure_messages


def _run_tests_in_worktree(
    worktree_dir: str,
    test_list: list[str],
    timeout: int = 300,
) -> dict:
    """Run specific pytest tests in a worktree.

    Args:
        worktree_dir: Path to the worktree
        test_list: List of test node IDs (e.g., ["tests/test_foo.py::test_bar"])
        timeout: Timeout in seconds

    Returns:
        Dict with stdout, stderr, returncode
    """
    cmd = [sys.executable, "-m", "pytest", "-xvs"] + test_list

    try:
        result = subprocess.run(
            cmd,
            cwd=worktree_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **dict(os.environ),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timeout": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "timeout": True,
        }


def _parse_test_ids(test_spec: str | list) -> list[str]:
    """Parse SWE-bench test specifications into pytest node IDs.

    SWE-bench stores tests as either a JSON list or space-separated string.

    Args:
        test_spec: Test specification (string or list)

    Returns:
        List of pytest node IDs
    """
    if isinstance(test_spec, list):
        return test_spec
    if isinstance(test_spec, str):
        try:
            parsed = json.loads(test_spec)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # Space or newline separated
        return [t.strip() for t in test_spec.split() if t.strip()]
    return []


def execute_swebench_solution(
    instance: dict,
    raw_model_output: str,
    repo_cache_dir: str | None = None,
    timeout: int = 300,
) -> dict:
    """Execute and evaluate a SWE-bench solution.

    Full pipeline:
    1. Extract modified files from model output
    2. Clone/cache the repo, create a worktree at base_commit
    3. Apply test_patch (if any) to add the expected test changes
    4. Apply model's modifications
    5. Run FAIL_TO_PASS tests (must now pass)
    6. Run PASS_TO_PASS tests (must still pass)
    7. Clean up worktree
    8. Return standard result dict

    Args:
        instance: SWE-bench instance dictionary
        raw_model_output: Raw model response text containing modified files
        repo_cache_dir: Directory for cached repos
        timeout: Timeout in seconds for test execution

    Returns:
        Result dictionary with standard fields plus SWE-bench extras
    """
    cache_dir = repo_cache_dir or os.path.expanduser("~/.koderz/swebench-repos")

    # Step 1: Extract modified files
    modifications = extract_modified_files(raw_model_output)
    if not modifications:
        return {
            "success": False,
            "tests_passed": 0,
            "tests_total": 0,
            "test_pass_rate": 0.0,
            "f2p_passed": 0,
            "f2p_total": 0,
            "p2p_passed": 0,
            "p2p_total": 0,
            "stdout": "",
            "stderr": "",
            "error": "No files could be extracted from model output",
            "patch": "",
            "files_modified": [],
        }

    repo = instance.get("repo", "")
    base_commit = instance.get("base_commit", "")
    test_patch = instance.get("test_patch", "")

    # Parse test lists
    f2p_tests = _parse_test_ids(instance.get("FAIL_TO_PASS", instance.get("fail_to_pass", [])))
    p2p_tests = _parse_test_ids(instance.get("PASS_TO_PASS", instance.get("pass_to_pass", [])))

    if not repo or not base_commit:
        return {
            "success": False,
            "tests_passed": 0,
            "tests_total": 0,
            "test_pass_rate": 0.0,
            "f2p_passed": 0,
            "f2p_total": len(f2p_tests),
            "p2p_passed": 0,
            "p2p_total": len(p2p_tests),
            "stdout": "",
            "stderr": "",
            "error": f"Missing repo ({repo!r}) or base_commit ({base_commit!r})",
            "patch": "",
            "files_modified": [m["path"] for m in modifications],
        }

    try:
        # Step 2: Clone repo + create worktree
        repo_dir = ensure_repo_clone(repo, cache_dir=cache_dir)
        instance_id = instance.get("instance_id", instance.get("task_id", "unknown"))
        worktree_name = instance_id.replace("/", "_").replace("__", "_")

        with worktree_context(repo_dir, base_commit, name=worktree_name, test_patch=test_patch or None) as wt_dir:
            # Step 3: Install project (best-effort)
            _best_effort_install(wt_dir)

            # Step 4: Apply model's modifications
            written = apply_modifications(wt_dir, modifications)

            # Step 5: Generate patch for export
            patch = generate_patch(wt_dir)

            # Step 6: Run FAIL_TO_PASS tests
            f2p_passed = 0
            f2p_total = len(f2p_tests)
            f2p_stdout = ""
            f2p_stderr = ""

            if f2p_tests:
                f2p_result = _run_tests_in_worktree(wt_dir, f2p_tests, timeout=timeout)
                f2p_stdout = f2p_result["stdout"]
                f2p_stderr = f2p_result["stderr"]

                if f2p_result["timeout"]:
                    f2p_passed = 0
                else:
                    f2p_passed_count, _, _ = parse_pytest_output(f2p_stdout, f2p_stderr)
                    f2p_passed = f2p_passed_count

            # Step 7: Run PASS_TO_PASS tests
            p2p_passed = 0
            p2p_total = len(p2p_tests)
            p2p_stdout = ""
            p2p_stderr = ""

            if p2p_tests:
                p2p_result = _run_tests_in_worktree(wt_dir, p2p_tests, timeout=timeout)
                p2p_stdout = p2p_result["stdout"]
                p2p_stderr = p2p_result["stderr"]

                if p2p_result["timeout"]:
                    p2p_passed = 0
                else:
                    p2p_passed_count, _, _ = parse_pytest_output(p2p_stdout, p2p_stderr)
                    p2p_passed = p2p_passed_count

        # Step 8: Compute results
        total_tests = f2p_total + p2p_total
        total_passed = f2p_passed + p2p_passed

        # Success requires ALL FAIL_TO_PASS pass AND ALL PASS_TO_PASS pass
        success = (f2p_passed == f2p_total and f2p_total > 0 and p2p_passed == p2p_total)

        combined_stdout = f2p_stdout + "\n" + p2p_stdout
        combined_stderr = f2p_stderr + "\n" + p2p_stderr

        error = None
        if not success:
            parts = []
            if f2p_passed < f2p_total:
                parts.append(f"FAIL_TO_PASS: {f2p_passed}/{f2p_total}")
            if p2p_passed < p2p_total:
                parts.append(f"PASS_TO_PASS: {p2p_passed}/{p2p_total}")
            error = "; ".join(parts) if parts else "Unknown failure"

        return {
            "success": success,
            "tests_passed": total_passed,
            "tests_total": total_tests,
            "test_pass_rate": total_passed / total_tests if total_tests > 0 else 0.0,
            "f2p_passed": f2p_passed,
            "f2p_total": f2p_total,
            "p2p_passed": p2p_passed,
            "p2p_total": p2p_total,
            "stdout": combined_stdout,
            "stderr": combined_stderr,
            "error": error,
            "patch": patch,
            "files_modified": written,
        }

    except Exception as e:
        return {
            "success": False,
            "tests_passed": 0,
            "tests_total": len(f2p_tests) + len(p2p_tests),
            "test_pass_rate": 0.0,
            "f2p_passed": 0,
            "f2p_total": len(f2p_tests),
            "p2p_passed": 0,
            "p2p_total": len(p2p_tests),
            "stdout": "",
            "stderr": "",
            "error": str(e),
            "patch": "",
            "files_modified": [m["path"] for m in modifications],
        }


def _best_effort_install(worktree_dir: str) -> None:
    """Best-effort pip install of the project in a worktree.

    Tries ``pip install -e .`` silently. Non-fatal on failure.

    Args:
        worktree_dir: Path to the worktree
    """
    setup_py = os.path.join(worktree_dir, "setup.py")
    setup_cfg = os.path.join(worktree_dir, "setup.cfg")
    pyproject = os.path.join(worktree_dir, "pyproject.toml")

    if not (os.path.exists(setup_py) or os.path.exists(setup_cfg) or os.path.exists(pyproject)):
        return

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet", "--no-deps"],
            cwd=worktree_dir,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
