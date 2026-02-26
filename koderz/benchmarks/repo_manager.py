"""Git repository management for SWE-bench evaluation.

Handles cloning repos, creating isolated worktrees for per-instance evaluation,
and reading files at specific commits.
"""

import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path


DEFAULT_REPO_CACHE = os.path.expanduser("~/.koderz/swebench-repos")


def ensure_repo_clone(repo: str, cache_dir: str = DEFAULT_REPO_CACHE) -> str:
    """Clone a GitHub repo if not already cached.

    Args:
        repo: GitHub repo in "owner/name" format (e.g., "django/django")
        cache_dir: Directory to cache cloned repos

    Returns:
        Path to the cloned repo directory
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Use owner__name as directory name to avoid conflicts
    repo_dir_name = repo.replace("/", "__")
    repo_dir = cache_path / repo_dir_name

    if repo_dir.exists() and (repo_dir / ".git").exists():
        # Already cloned, fetch latest
        try:
            subprocess.run(
                ["git", "fetch", "--all"],
                cwd=str(repo_dir),
                capture_output=True,
                timeout=120,
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass  # Non-fatal, we already have the repo
        return str(repo_dir)

    # Clone fresh
    url = f"https://github.com/{repo}.git"
    subprocess.run(
        ["git", "clone", "--bare", url, str(repo_dir)],
        check=True,
        capture_output=True,
        timeout=600,
    )

    return str(repo_dir)


@contextmanager
def worktree_context(repo_dir: str, commit: str, name: str = "", test_patch: str | None = None):
    """Create a detached git worktree, yield its path, then clean up.

    Uses git worktree for fast, isolated evaluation that shares the object store
    with the cached bare clone.

    Args:
        repo_dir: Path to the bare clone
        commit: Commit hash to check out
        name: Optional name suffix for the worktree directory
        test_patch: Optional unified diff to apply (e.g., test patches for SWE-bench)

    Yields:
        Path to the worktree directory
    """
    if not name:
        name = uuid.uuid4().hex[:8]

    worktree_dir = os.path.join(tempfile.gettempdir(), f"koderz-swe-{name}")

    try:
        # Create detached worktree at the specified commit
        subprocess.run(
            ["git", "worktree", "add", "--detach", worktree_dir, commit],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Apply test patch if provided
        if test_patch:
            proc = subprocess.run(
                ["git", "apply", "--allow-empty", "-"],
                input=test_patch,
                cwd=worktree_dir,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                # Try with --3way as fallback for patches that need it
                subprocess.run(
                    ["git", "apply", "--3way", "-"],
                    input=test_patch,
                    cwd=worktree_dir,
                    capture_output=True,
                    text=True,
                )

        yield worktree_dir

    finally:
        # Clean up worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_dir],
                cwd=repo_dir,
                capture_output=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback: just remove the directory
            import shutil
            if os.path.exists(worktree_dir):
                shutil.rmtree(worktree_dir, ignore_errors=True)
            # Prune stale worktree entries
            try:
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=repo_dir,
                    capture_output=True,
                    timeout=10,
                )
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass


def read_file_at_commit(repo_dir: str, commit: str, filepath: str) -> str:
    """Read a file's contents at a specific commit.

    Args:
        repo_dir: Path to the git repo (bare or regular)
        commit: Commit hash
        filepath: Path relative to repo root

    Returns:
        File contents as string

    Raises:
        subprocess.CalledProcessError: If the file doesn't exist at that commit
    """
    result = subprocess.run(
        ["git", "show", f"{commit}:{filepath}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
