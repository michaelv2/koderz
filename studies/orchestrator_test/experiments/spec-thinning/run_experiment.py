#!/usr/bin/env python3
"""
Spec-thinning experiment: test spec detail vs gotchas vs iteration.

Four spec arms × N models, with optional iterative fix loop.

Usage:
    # Single-shot, all arms, default models
    python experiments/spec-thinning/run_experiment.py

    # With iteration (up to 3 fix attempts per arm)
    python experiments/spec-thinning/run_experiment.py --max-iter 3

    # Specific model and arm
    python experiments/spec-thinning/run_experiment.py --model qwen3-coder:latest --arm arm_d

    # Save results to file
    python experiments/spec-thinning/run_experiment.py --output results.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXPERIMENT_DIR))
AGENTMON_DIR = os.path.join(PROJECT_ROOT, "agentmon")
TESTS = "tests/test_agentmon_acceptance.py::TestDataModels tests/test_agentmon_acceptance.py::TestEventStore"

ARMS = {
    "arm_a": {
        "label": "Thin logic + Rich gotchas",
        "spec": os.path.join(EXPERIMENT_DIR, "arm_a_thin_logic_rich_gotchas.md"),
    },
    "arm_b": {
        "label": "Rich logic + Thin gotchas",
        "spec": os.path.join(EXPERIMENT_DIR, "arm_b_rich_logic_thin_gotchas.md"),
    },
    "arm_c": {
        "label": "Uniformly thin",
        "spec": os.path.join(EXPERIMENT_DIR, "arm_c_uniformly_thin.md"),
    },
    "arm_d": {
        "label": "Thin structure + Gotchas",
        "spec": os.path.join(EXPERIMENT_DIR, "arm_d_thin_plus_gotchas.md"),
    },
}

MODELS = [
    "gpt-oss:20b-128k",
    "qwen3-coder:latest",
]

HOST = "http://192.168.1.74:11434"


def clean_agentmon():
    """Remove agentmon/ directory for a clean run."""
    if os.path.exists(AGENTMON_DIR):
        shutil.rmtree(AGENTMON_DIR)


def call_orchestrate(spec_path: str, model: str, context_files: list[str] = None) -> dict:
    """Call orchestrate_subtask.py and return parsed JSON result."""
    cmd = [
        sys.executable, os.path.join(PROJECT_ROOT, "scripts", "orchestrate_subtask.py"),
        "--spec", spec_path,
        "--tests", TESTS,
        "--model", model,
        "--host", HOST,
    ]
    if context_files:
        cmd += ["--context"] + context_files

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        cwd=PROJECT_ROOT,
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "error": "JSON parse failed",
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500],
        }


def extract_failed_tests(data: dict) -> list[str]:
    """Extract failed test names from orchestrate_subtask output."""
    failed = []
    if not data.get("success") and data.get("test_output"):
        for line in data["test_output"].split("\n"):
            if line.startswith("FAILED "):
                failed.append(line.replace("FAILED ", "").split(" ")[0])
    return failed


def generate_fix_spec(test_output: str, failed_tests: list[str]) -> str:
    """Generate an automated fix spec from test failure output."""
    lines = [
        "# Fix: failing tests",
        "",
        "The current code has test failures. Fix the issues described below.",
        "Rewrite the complete files — do not use partial snippets.",
        "Put `# path/to/file.py` as the first line in each code block.",
        "",
        "## Failing tests",
        "",
    ]
    for t in failed_tests:
        lines.append(f"- `{t}`")
    lines.append("")
    lines.append("## Test output")
    lines.append("")
    lines.append("```")
    # Truncate very long output to keep prompt reasonable
    if len(test_output) > 4000:
        lines.append(test_output[:4000])
        lines.append("... (truncated)")
    else:
        lines.append(test_output)
    lines.append("```")
    return "\n".join(lines)


def get_written_files() -> list[str]:
    """Get list of .py files in agentmon/ directory (relative paths)."""
    files = []
    if not os.path.exists(AGENTMON_DIR):
        return files
    for root, dirs, filenames in os.walk(AGENTMON_DIR):
        for f in filenames:
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, f), PROJECT_ROOT)
                files.append(rel)
    return sorted(files)


def run_arm(arm_name: str, arm: dict, model: str, max_iter: int = 1) -> dict:
    """Run one arm of the experiment, with optional iteration."""
    clean_agentmon()

    print(f"\n{'='*70}", file=sys.stderr)
    print(f"  {arm_name}: {arm['label']}", file=sys.stderr)
    print(f"  Model: {model}  |  Max iterations: {max_iter}", file=sys.stderr)
    print(f"{'='*70}", file=sys.stderr)

    total_start = time.time()
    iterations = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # --- Iteration 0: initial attempt ---
    print("  [iter 0] Initial attempt...", file=sys.stderr)
    iter_start = time.time()
    data = call_orchestrate(arm["spec"], model)
    iter_elapsed = time.time() - iter_start

    if "error" in data and "JSON parse failed" in data.get("error", ""):
        print("  ERROR: couldn't parse JSON output", file=sys.stderr)
        return {
            "arm": arm_name,
            "label": arm["label"],
            "model": model,
            "max_iter": max_iter,
            "error": "JSON parse failed",
            "stderr": data.get("stderr", "")[:1000],
        }

    failed_tests = extract_failed_tests(data)
    total_prompt_tokens += data.get("worker_tokens", {}).get("prompt", 0)
    total_completion_tokens += data.get("worker_tokens", {}).get("completion", 0)

    iterations.append({
        "iter": 0,
        "tests_passed": data.get("tests_passed", 0),
        "tests_failed": data.get("tests_failed", 0),
        "tests_error": data.get("tests_error", 0),
        "success": data.get("success", False),
        "failed_tests": failed_tests,
        "prompt_tokens": data.get("worker_tokens", {}).get("prompt", 0),
        "completion_tokens": data.get("worker_tokens", {}).get("completion", 0),
        "time_seconds": round(iter_elapsed, 1),
    })

    status = "PASS" if data.get("success") else f"FAIL ({data.get('tests_passed', 0)}/18)"
    print(f"  [iter 0] {status}", file=sys.stderr)

    # --- Fix iterations ---
    for i in range(1, max_iter):
        if data.get("success"):
            break

        print(f"  [iter {i}] Fix attempt...", file=sys.stderr)

        # Generate fix spec from test output
        fix_text = generate_fix_spec(
            data.get("test_output", ""),
            failed_tests,
        )

        # Write fix spec to temp file
        fix_fd, fix_path = tempfile.mkstemp(suffix=".md", prefix=f"fix_iter{i}_")
        with os.fdopen(fix_fd, "w") as f:
            f.write(fix_text)

        # Get context files (whatever the previous iteration wrote)
        context_files = get_written_files()

        iter_start = time.time()
        try:
            data = call_orchestrate(fix_path, model, context_files=context_files)
        finally:
            os.unlink(fix_path)
        iter_elapsed = time.time() - iter_start

        if "error" in data and "JSON parse failed" in data.get("error", ""):
            print(f"  [iter {i}] ERROR: JSON parse failed", file=sys.stderr)
            iterations.append({"iter": i, "error": "JSON parse failed"})
            break

        failed_tests = extract_failed_tests(data)
        total_prompt_tokens += data.get("worker_tokens", {}).get("prompt", 0)
        total_completion_tokens += data.get("worker_tokens", {}).get("completion", 0)

        iterations.append({
            "iter": i,
            "tests_passed": data.get("tests_passed", 0),
            "tests_failed": data.get("tests_failed", 0),
            "tests_error": data.get("tests_error", 0),
            "success": data.get("success", False),
            "failed_tests": failed_tests,
            "prompt_tokens": data.get("worker_tokens", {}).get("prompt", 0),
            "completion_tokens": data.get("worker_tokens", {}).get("completion", 0),
            "time_seconds": round(iter_elapsed, 1),
        })

        status = "PASS" if data.get("success") else f"FAIL ({data.get('tests_passed', 0)}/18)"
        print(f"  [iter {i}] {status}", file=sys.stderr)

    total_elapsed = time.time() - total_start

    # Build final entry from last iteration's data
    last_iter = iterations[-1]
    entry = {
        "arm": arm_name,
        "label": arm["label"],
        "model": model,
        "max_iter": max_iter,
        "iterations_used": len(iterations),
        "tests_passed": last_iter.get("tests_passed", 0),
        "tests_failed": last_iter.get("tests_failed", 0),
        "tests_error": last_iter.get("tests_error", 0),
        "total_tests": 18,
        "pass_rate": f"{last_iter.get('tests_passed', 0)}/18",
        "success": last_iter.get("success", False),
        "failed_tests": last_iter.get("failed_tests", []),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_time_seconds": round(total_elapsed, 1),
        "iterations": iterations,
    }

    if failed_tests:
        print(f"  Final failed: {', '.join(failed_tests)}", file=sys.stderr)
    print(
        f"  Total tokens: {total_prompt_tokens}+{total_completion_tokens}  "
        f"Time: {total_elapsed:.1f}s  Iters: {len(iterations)}",
        file=sys.stderr,
    )

    return entry


def main():
    parser = argparse.ArgumentParser(description="Spec-thinning experiment")
    parser.add_argument("--model", help="Run only this model")
    parser.add_argument("--arm", help="Run only this arm (arm_a, arm_b, arm_c, arm_d)")
    parser.add_argument(
        "--max-iter", type=int, default=1,
        help="Max iterations per arm (1=single-shot, 3=two fix attempts)",
    )
    parser.add_argument("--output", help="Save JSON results to this file")
    args = parser.parse_args()

    models = [args.model] if args.model else MODELS
    arms = {args.arm: ARMS[args.arm]} if args.arm else ARMS

    results = []
    for model in models:
        for arm_name, arm in arms.items():
            entry = run_arm(arm_name, arm, model, max_iter=args.max_iter)
            results.append(entry)

    # Clean up after experiment
    clean_agentmon()

    # Summary table
    print(f"\n{'='*70}", file=sys.stderr)
    print("RESULTS", file=sys.stderr)
    print(f"{'='*70}", file=sys.stderr)
    iter_label = "Iters" if args.max_iter > 1 else ""
    print(
        f"{'Arm':<12} {'Model':<22} {'Pass':>6} {'Prompt':>7} {'Compl':>7} "
        f"{'Time':>6} {iter_label:>5}",
        file=sys.stderr,
    )
    print("-" * 75, file=sys.stderr)
    for r in results:
        if "error" in r:
            print(f"{r['arm']:<12} {r['model']:<22} ERROR", file=sys.stderr)
            continue
        iter_str = f"{r['iterations_used']}" if args.max_iter > 1 else ""
        print(
            f"{r['arm']:<12} {r['model']:<22} {r['pass_rate']:>6} "
            f"{r['total_prompt_tokens']:>7} {r['total_completion_tokens']:>7} "
            f"{r['total_time_seconds']:>5}s {iter_str:>5}",
            file=sys.stderr,
        )

    # JSON output
    output = json.dumps(results, indent=2)
    print(output)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"\nResults saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
