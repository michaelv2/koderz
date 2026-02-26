#!/usr/bin/env python3
"""
Orchestrate a single subtask: call worker model, extract files, write them, run tests.

Combines the worker call, file extraction, file writing, and test running into one
command so the orchestrator can delegate all mechanical work in a single shell call.

Usage:
    # Basic: spec file + test pattern
    python scripts/orchestrate_subtask.py \
        --spec specs/subtask1.md \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels tests/test_agentmon_acceptance.py::TestEventStore"

    # Fix with context: short fix spec + current files injected automatically
    python scripts/orchestrate_subtask.py \
        --spec specs/subtask1_fix.md \
        --context agentmon/storage/db.py agentmon/models/events.py \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels"

    # With model/host override
    python scripts/orchestrate_subtask.py \
        --spec specs/subtask1.md \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
        --model gpt-oss:20b-128k \
        --host http://192.168.1.74:11434

    # Save raw worker output for analysis
    python scripts/orchestrate_subtask.py \
        --spec specs/subtask1.md \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
        --save-raw raw_output.txt

    # Skip worker call, just run tests on already-written files
    python scripts/orchestrate_subtask.py \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
        --test-only

    # With Haiku diagnostic: auto-diagnose failures and retry up to N times
    python scripts/orchestrate_subtask.py \
        --spec specs/subtask1.md \
        --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
        --diagnose --max-retries 2

Output: JSON to stdout with files_written, test results, pass/fail counts, timing.
When --diagnose is used, JSON also includes retries, diagnostic_tokens, iterations.
All progress messages go to stderr.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

# Import from sibling module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ollama_worker import call_ollama


DEFAULT_MODEL = "qwen3-coder:latest"
DEFAULT_HOST = "http://192.168.1.74:11434"
DEFAULT_DIAGNOSE_MODEL = "claude-haiku-4-5-20251001"


def build_prompt(spec: str, context_files: list[str], base_dir: str = ".") -> str:
    """Build the full prompt by prepending context files before the spec.

    If context_files is non-empty, reads each file from disk and prepends it
    as a labeled section. The spec follows after all context.
    """
    if not context_files:
        return spec

    parts = ["# Current files for reference\n"]
    for path in context_files:
        full_path = os.path.join(base_dir, path)
        try:
            with open(full_path) as f:
                content = f.read()
            parts.append(f"## `{path}`\n```python\n{content}```\n")
        except FileNotFoundError:
            parts.append(f"## `{path}` (file not found)\n")

    parts.append("# Task\n")
    parts.append(spec)
    return "\n".join(parts)


def _normalize_path(raw_path: str) -> str:
    """Strip leading 'path/to/' or similar placeholder prefixes from a file path."""
    # Remove common placeholder prefixes like "path/to/"
    cleaned = re.sub(r"^(?:path/to/)+", "", raw_path)
    return cleaned


def extract_files_from_response(content: str) -> list[dict]:
    """Extract file paths and code from fenced code blocks in worker response.

    Supports path comments inside the code block:
        ```python
        # agentmon/models/events.py
        ...code...
        ```

    Also supports paths on the line immediately before the code fence:
        # agentmon/models/events.py
        ```python
        ...code...
        ```

    Also handles "File:" prefix and "path/to/" placeholder prefixes.

    Returns list of {"path": "agentmon/...", "code": "..."} dicts.
    Blocks without a recognized path comment are skipped.
    """
    PATH_RE = r"^#\s*(?:File:\s*)?(\S+\.py)\s*$"

    files = []

    # Split content into lines to handle both inside-fence and before-fence patterns
    content_lines = content.split("\n")
    i = 0
    while i < len(content_lines):
        line = content_lines[i]

        # Check if this line opens a code fence
        if re.match(r"^```(?:python)?\s*$", line.strip()):
            fence_start = i
            # Collect block contents until closing fence
            block_lines = []
            i += 1
            while i < len(content_lines) and not content_lines[i].strip().startswith("```"):
                block_lines.append(content_lines[i])
                i += 1
            i += 1  # skip closing ```

            if not block_lines:
                continue

            path = None

            # Strategy 1: path on first line inside the block
            first_line = block_lines[0].strip()
            path_match = re.match(PATH_RE, first_line)
            if path_match:
                path = _normalize_path(path_match.group(1))
                code = "\n".join(block_lines[1:]).strip() + "\n"
            else:
                code = "\n".join(block_lines).strip() + "\n"

            # Strategy 2: path on line(s) immediately before the fence
            if not path:
                for j in range(fence_start - 1, max(fence_start - 4, -1), -1):
                    if j < 0:
                        break
                    prev = content_lines[j].strip()
                    if not prev:
                        continue
                    prev_match = re.match(PATH_RE, prev)
                    if prev_match:
                        path = _normalize_path(prev_match.group(1))
                    break

            if path:
                files.append({"path": path, "code": code})
        else:
            i += 1

    return files


def write_files(files: list[dict], base_dir: str = ".") -> list[str]:
    """Write extracted files to disk, creating directories as needed.

    Returns list of paths written.
    """
    written = []
    for f in files:
        full_path = os.path.join(base_dir, f["path"])
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as fh:
            fh.write(f["code"])
        written.append(f["path"])

        # Ensure __init__.py exists in every package directory
        parts = f["path"].split("/")
        for i in range(1, len(parts)):
            pkg_dir = os.path.join(base_dir, *parts[:i])
            init_path = os.path.join(pkg_dir, "__init__.py")
            if os.path.isdir(pkg_dir) and not os.path.exists(init_path):
                with open(init_path, "w") as fh:
                    fh.write("")

    return written


def run_tests(test_patterns: list[str], timeout: int = 120) -> dict:
    """Run pytest with the given test patterns and return structured results.

    Returns dict with tests_passed, tests_failed, tests_error, test_output, success.
    """
    cmd = [sys.executable, "-m", "pytest", "-v"] + test_patterns

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_error": 0,
            "test_output": f"pytest timed out after {timeout}s",
            "success": False,
        }

    output = result.stdout + result.stderr

    # Parse pytest summary line: "X passed, Y failed, Z error"
    passed = 0
    failed = 0
    errors = 0

    summary_match = re.search(
        r"(\d+) passed", output
    )
    if summary_match:
        passed = int(summary_match.group(1))

    fail_match = re.search(r"(\d+) failed", output)
    if fail_match:
        failed = int(fail_match.group(1))

    error_match = re.search(r"(\d+) error", output)
    if error_match:
        errors = int(error_match.group(1))

    success = result.returncode == 0

    # On success, return just the summary. On failure, return full output.
    if success:
        # Extract just the last few lines (summary)
        lines = output.strip().split("\n")
        # Find the short test summary or final result line
        summary_lines = []
        for i, line in enumerate(lines):
            if line.startswith("=") and ("passed" in line or "failed" in line):
                summary_lines = lines[max(0, i - 1) :]
                break
        test_output = "\n".join(summary_lines) if summary_lines else lines[-1]
    else:
        test_output = output

    return {
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_error": errors,
        "test_output": test_output,
        "success": success,
    }


def call_diagnostic(
    original_spec: str,
    test_output: str,
    written_files: list[str],
    base_dir: str = ".",
    model: str = DEFAULT_DIAGNOSE_MODEL,
) -> dict:
    """Call Haiku to diagnose test failures and produce a targeted fix spec.

    Uses the Anthropic Messages API directly via httpx.

    Returns dict with "fix_spec", "prompt_tokens", "completion_tokens".
    """
    import httpx

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — required for --diagnose")

    # Build file contents section
    file_sections = []
    for path in written_files:
        full_path = os.path.join(base_dir, path)
        try:
            with open(full_path) as f:
                content = f.read()
            file_sections.append(f"## `{path}`\n```python\n{content}```")
        except FileNotFoundError:
            file_sections.append(f"## `{path}` (file not found)")

    file_text = "\n\n".join(file_sections) if file_sections else "(no files written)"

    # Truncate test output to ~4000 chars
    if len(test_output) > 4000:
        test_output = test_output[:4000] + "\n... (truncated)"

    user_message = (
        f"# Original Spec\n\n{original_spec}\n\n"
        f"# Test Output\n\n```\n{test_output}\n```\n\n"
        f"# Current Files\n\n{file_text}"
    )

    system_prompt = (
        "You are a code diagnostic assistant. Analyze test failures and write a "
        "concise fix spec for a worker model. Output ONLY the fix spec text — no "
        "explanations, no code. The fix spec should describe what's wrong and what "
        "to change, in 10-20 lines."
    )

    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    fix_spec = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            fix_spec += block["text"]

    usage = data.get("usage", {})

    return {
        "fix_spec": fix_spec,
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate subtask: worker call + file write + test run"
    )
    parser.add_argument(
        "--spec", help="Path to spec/prompt file to send to worker model"
    )
    parser.add_argument(
        "--tests",
        required=True,
        help="Space-separated pytest node IDs (e.g. 'tests/test.py::TestFoo tests/test.py::TestBar')",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--system",
        default="You are an expert Python developer. Write clean, correct code. "
        "Always wrap code in ```python fenced blocks. "
        "Put a # path/to/file.py comment as the FIRST line inside each code block.",
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--timeout", type=int, default=300, help="Worker call timeout")
    parser.add_argument(
        "--test-timeout", type=int, default=120, help="Pytest timeout"
    )
    parser.add_argument(
        "--context",
        nargs="+",
        default=[],
        help="File paths to prepend as context before the spec (e.g. agentmon/storage/db.py)",
    )
    parser.add_argument(
        "--save-raw", help="Save raw worker response to this file"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Skip worker call, only run tests on existing files",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory for writing files (default: current dir)",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Enable Haiku diagnostic step on test failures",
    )
    parser.add_argument(
        "--diagnose-model",
        default=DEFAULT_DIAGNOSE_MODEL,
        help=f"Model for diagnosis (default: {DEFAULT_DIAGNOSE_MODEL})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Max fix iterations when --diagnose is set (default: 2)",
    )
    args = parser.parse_args()

    result = {
        "files_written": [],
        "worker_tokens": {"prompt": 0, "completion": 0},
        "worker_time_seconds": 0,
        "test_pattern": args.tests,
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_error": 0,
        "test_output": "",
        "success": False,
    }

    # Diagnostic tracking (populated only when --diagnose is used)
    diagnostic_tokens = {"prompt": 0, "completion": 0}
    iterations = []

    test_patterns = args.tests.split()

    # --- Step 1: Call worker (unless --test-only) ---
    if not args.test_only:
        if not args.spec:
            print("Error: --spec is required unless --test-only is set", file=sys.stderr)
            sys.exit(1)

        with open(args.spec) as f:
            spec_text = f.read()

        if not spec_text.strip():
            print("Error: spec file is empty", file=sys.stderr)
            sys.exit(1)

        prompt = build_prompt(spec_text, args.context, base_dir=args.base_dir)

        if args.context:
            print(
                f"Injected {len(args.context)} context file(s): {', '.join(args.context)}",
                file=sys.stderr,
            )

        print(f"Calling {args.model} on {args.host}...", file=sys.stderr)
        start = time.time()

        try:
            worker_result = call_ollama(
                prompt=prompt,
                model=args.model,
                host=args.host,
                system=args.system,
                temperature=args.temperature,
                num_ctx=args.num_ctx,
                timeout=args.timeout,
            )
        except Exception as e:
            print(f"Worker call failed: {e}", file=sys.stderr)
            result["test_output"] = f"Worker call failed: {e}"
            print(json.dumps(result, indent=2))
            sys.exit(1)

        elapsed = time.time() - start
        result["worker_tokens"] = {
            "prompt": worker_result["prompt_tokens"],
            "completion": worker_result["completion_tokens"],
        }
        result["worker_time_seconds"] = round(elapsed, 1)

        print(
            f"Worker done in {elapsed:.1f}s "
            f"({worker_result['prompt_tokens']} prompt + "
            f"{worker_result['completion_tokens']} completion tokens)",
            file=sys.stderr,
        )

        # Save raw output if requested
        if args.save_raw:
            with open(args.save_raw, "w") as f:
                f.write(worker_result["content"])
            print(f"Raw output saved to {args.save_raw}", file=sys.stderr)

        # --- Step 2: Extract and write files ---
        files = extract_files_from_response(worker_result["content"])
        if not files:
            print(
                "Warning: no files extracted from worker response", file=sys.stderr
            )
            result["test_output"] = (
                "No files could be extracted from worker response. "
                "Worker output starts with: "
                + worker_result["content"][:500]
            )
            print(json.dumps(result, indent=2))
            sys.exit(0)

        written = write_files(files, base_dir=args.base_dir)
        result["files_written"] = written
        print(f"Wrote {len(written)} files: {', '.join(written)}", file=sys.stderr)

    # --- Step 3: Run tests ---
    print(f"Running tests: {' '.join(test_patterns)}", file=sys.stderr)

    test_result = run_tests(test_patterns, timeout=args.test_timeout)
    result.update(test_result)

    status = "PASS" if result["success"] else "FAIL"
    print(
        f"Tests: {status} "
        f"({result['tests_passed']} passed, {result['tests_failed']} failed, "
        f"{result['tests_error']} errors)",
        file=sys.stderr,
    )

    if args.diagnose:
        iterations.append({
            "iter": 0,
            "tests_passed": result["tests_passed"],
            "tests_failed": result["tests_failed"],
        })

    # --- Step 4: Diagnostic retry loop (when --diagnose is enabled) ---
    if args.diagnose and not result["success"] and not args.test_only:
        for retry in range(1, args.max_retries + 1):
            print(
                f"\n--- Diagnostic retry {retry}/{args.max_retries} ---",
                file=sys.stderr,
            )

            # 4a: Call Haiku for diagnosis
            print(
                f"Calling {args.diagnose_model} for diagnosis...", file=sys.stderr
            )
            try:
                diag = call_diagnostic(
                    original_spec=spec_text,
                    test_output=result["test_output"],
                    written_files=result["files_written"],
                    base_dir=args.base_dir,
                    model=args.diagnose_model,
                )
            except Exception as e:
                print(f"Diagnostic call failed: {e}", file=sys.stderr)
                break

            diagnostic_tokens["prompt"] += diag["prompt_tokens"]
            diagnostic_tokens["completion"] += diag["completion_tokens"]

            fix_spec = diag["fix_spec"]
            print(
                f"Diagnostic done ({diag['prompt_tokens']} prompt + "
                f"{diag['completion_tokens']} completion tokens)",
                file=sys.stderr,
            )
            print(f"Fix spec ({len(fix_spec.splitlines())} lines):", file=sys.stderr)
            for line in fix_spec.splitlines()[:5]:
                print(f"  {line}", file=sys.stderr)
            if len(fix_spec.splitlines()) > 5:
                print(f"  ... ({len(fix_spec.splitlines()) - 5} more lines)", file=sys.stderr)

            # 4b: Write fix spec to temp file, call worker with --context
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, prefix="fix_spec_"
            ) as tmp:
                tmp.write(fix_spec)
                fix_spec_path = tmp.name

            try:
                fix_prompt = build_prompt(
                    fix_spec, result["files_written"], base_dir=args.base_dir
                )

                print(f"Calling {args.model} with fix spec...", file=sys.stderr)
                start = time.time()

                worker_result = call_ollama(
                    prompt=fix_prompt,
                    model=args.model,
                    host=args.host,
                    system=args.system,
                    temperature=args.temperature,
                    num_ctx=args.num_ctx,
                    timeout=args.timeout,
                )

                elapsed = time.time() - start
                result["worker_tokens"]["prompt"] += worker_result["prompt_tokens"]
                result["worker_tokens"]["completion"] += worker_result["completion_tokens"]
                result["worker_time_seconds"] = round(
                    result["worker_time_seconds"] + elapsed, 1
                )

                print(
                    f"Worker done in {elapsed:.1f}s "
                    f"({worker_result['prompt_tokens']} prompt + "
                    f"{worker_result['completion_tokens']} completion tokens)",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"Worker call failed on retry: {e}", file=sys.stderr)
                break
            finally:
                os.unlink(fix_spec_path)

            # 4c: Extract and write files
            files = extract_files_from_response(worker_result["content"])
            if files:
                written = write_files(files, base_dir=args.base_dir)
                # Merge newly written files into the list (deduplicated)
                existing = set(result["files_written"])
                for w in written:
                    if w not in existing:
                        result["files_written"].append(w)
                print(
                    f"Wrote {len(written)} files: {', '.join(written)}",
                    file=sys.stderr,
                )
            else:
                print(
                    "Warning: no files extracted from retry response",
                    file=sys.stderr,
                )

            # 4d: Re-run tests
            print(f"Running tests: {' '.join(test_patterns)}", file=sys.stderr)
            test_result = run_tests(test_patterns, timeout=args.test_timeout)
            result.update(test_result)

            status = "PASS" if result["success"] else "FAIL"
            print(
                f"Tests: {status} "
                f"({result['tests_passed']} passed, {result['tests_failed']} failed, "
                f"{result['tests_error']} errors)",
                file=sys.stderr,
            )

            iterations.append({
                "iter": retry,
                "tests_passed": result["tests_passed"],
                "tests_failed": result["tests_failed"],
            })

            if result["success"]:
                print(f"Fixed on retry {retry}!", file=sys.stderr)
                break

    # --- Add diagnostic metadata to result ---
    if args.diagnose:
        result["retries"] = len(iterations) - 1  # iter 0 is the initial attempt
        result["diagnostic_tokens"] = diagnostic_tokens
        result["diagnostic_model"] = args.diagnose_model
        result["iterations"] = iterations

    # --- Output structured JSON ---
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
