#!/usr/bin/env python3
"""
Test: Can a 20B model reproduce a file verbatim while making a targeted change?

For each test case:
1. Give the model a Python file + a specific 1-line change instruction
2. Ask it to reproduce the entire file with only that change
3. Diff the output against the expected result
4. Report: intended change made? Unintended changes introduced?

Uses real files from B3 run as test material, spanning 55-313 lines.
"""

import difflib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ollama_worker import call_ollama

B3_DIR = "orchestrator_test/agentmon_b3"

# Each test case: (file, change instruction, line to change, old text, new text)
TEST_CASES = [
    {
        "name": "small_55L_rename_method",
        "file": f"{B3_DIR}/models/events.py",
        "instruction": "Rename the method `domain_parts` to `split_domain`.",
        "verify_old": "def domain_parts",
        "verify_new": "def split_domain",
    },
    {
        "name": "medium_96L_change_constant",
        "file": f"{B3_DIR}/analyzers/entropy.py",
        "instruction": "Change the DGA entropy threshold from its current value to 4.0.",
        "verify_old": None,  # We'll check the output contains 4.0
        "verify_new": "4.0",
    },
    {
        "name": "medium_121L_add_import",
        "file": f"{B3_DIR}/analyzers/dns_baseline.py",
        "instruction": "Add `import logging` at the top of the file (after the existing imports) and add `logger = logging.getLogger(__name__)` right after the imports.",
        "verify_old": None,
        "verify_new": "import logging",
    },
    {
        "name": "large_229L_fix_method",
        "file": f"{B3_DIR}/collectors/syslog_receiver.py",
        "instruction": "In the `parse_syslog_message` function, for RFC 3164 messages, replace the timestamp parsing logic with just `ts = datetime.utcnow()` (use reception time instead of parsed time).",
        "verify_old": None,
        "verify_new": "ts = datetime.utcnow()",
    },
    {
        "name": "large_313L_fix_one_method",
        "file": f"{B3_DIR}/storage/db.py",
        "instruction": "In the `cleanup_old_data` method, replace `.rowcount` usage with SELECT COUNT(*) before each DELETE. Count matching rows first, then delete.",
        "verify_old": None,
        "verify_new": "SELECT COUNT",
    },
]


def extract_code(response: str) -> str:
    """Extract the first Python code block from response."""
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
    if blocks:
        # Skip path comment if present
        code = blocks[0]
        lines = code.split("\n")
        if lines and re.match(r"^#\s*\S+\.py", lines[0]):
            code = "\n".join(lines[1:])
        return code.strip() + "\n"
    return response.strip() + "\n"


def compute_diff(original: str, reproduced: str) -> dict:
    """Compare original and reproduced, return diff stats."""
    orig_lines = original.splitlines(keepends=True)
    repr_lines = reproduced.splitlines(keepends=True)

    diff = list(difflib.unified_diff(orig_lines, repr_lines, n=0))

    added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

    # Semantic diff: ignore whitespace-only changes
    orig_stripped = [l.rstrip() for l in original.splitlines()]
    repr_stripped = [l.rstrip() for l in reproduced.splitlines()]
    semantic_diff = list(
        difflib.unified_diff(orig_stripped, repr_stripped, n=0)
    )
    semantic_added = sum(
        1 for l in semantic_diff if l.startswith("+") and not l.startswith("+++")
    )
    semantic_removed = sum(
        1 for l in semantic_diff if l.startswith("-") and not l.startswith("---")
    )

    return {
        "lines_added": added,
        "lines_removed": removed,
        "semantic_lines_added": semantic_added,
        "semantic_lines_removed": semantic_removed,
        "diff_preview": "".join(diff[:40]),
    }


def run_test(case: dict, model: str, host: str) -> dict:
    """Run a single reproduction test case."""
    file_path = case["file"]
    with open(file_path) as f:
        original = f.read()

    line_count = len(original.splitlines())

    prompt = f"""Here is the current content of `{file_path}`:

```python
{original}```

**Task**: {case['instruction']}

Reproduce the COMPLETE file with ONLY this change. Do not add, remove, or modify anything else.
Put `# {os.path.basename(file_path)}` as the first line inside the code block.
"""

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Test: {case['name']} ({line_count} lines)", file=sys.stderr)
    print(f"File: {file_path}", file=sys.stderr)
    print(f"Change: {case['instruction']}", file=sys.stderr)
    print(f"Calling {model}...", file=sys.stderr)

    start = time.time()
    result = call_ollama(
        prompt=prompt,
        model=model,
        host=host,
        system="You are an expert Python developer. Reproduce files exactly as given, making only the requested change. Wrap output in ```python fenced blocks.",
        temperature=0.1,  # Low temp for reproduction accuracy
    )
    elapsed = time.time() - start

    reproduced = extract_code(result["content"])

    # Check intended change
    intended_made = case["verify_new"] in reproduced
    old_still_present = case["verify_old"] in reproduced if case["verify_old"] else False

    # Compute diff against original
    diff_stats = compute_diff(original, reproduced)

    # "Unintended changes" = total semantic changes minus the 1-2 lines we expected to change
    # Rough heuristic: if we asked for 1 change, expect ~1-2 lines added/removed
    expected_churn = 3  # generous allowance for the intended change
    unintended_churn = max(
        0,
        diff_stats["semantic_lines_added"]
        + diff_stats["semantic_lines_removed"]
        - expected_churn,
    )

    test_result = {
        "name": case["name"],
        "file": file_path,
        "original_lines": line_count,
        "reproduced_lines": len(reproduced.splitlines()),
        "intended_change_made": intended_made,
        "old_code_still_present": old_still_present,
        "lines_added": diff_stats["semantic_lines_added"],
        "lines_removed": diff_stats["semantic_lines_removed"],
        "unintended_churn": unintended_churn,
        "worker_time_seconds": round(elapsed, 1),
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
    }

    # Print summary
    status = "PASS" if intended_made and unintended_churn == 0 else "FAIL"
    print(f"Result: {status}", file=sys.stderr)
    print(
        f"  Intended change made: {intended_made}", file=sys.stderr
    )
    print(
        f"  Lines: {line_count} original → {len(reproduced.splitlines())} reproduced",
        file=sys.stderr,
    )
    print(
        f"  Semantic diff: +{diff_stats['semantic_lines_added']} "
        f"-{diff_stats['semantic_lines_removed']}",
        file=sys.stderr,
    )
    print(f"  Unintended churn: {unintended_churn} lines", file=sys.stderr)
    print(
        f"  Time: {elapsed:.1f}s "
        f"({result['prompt_tokens']}+{result['completion_tokens']} tokens)",
        file=sys.stderr,
    )

    if diff_stats["diff_preview"]:
        print("  Diff preview:", file=sys.stderr)
        for line in diff_stats["diff_preview"].splitlines()[:20]:
            print(f"    {line}", file=sys.stderr)

    return test_result


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Test verbatim file reproduction accuracy of local models"
    )
    parser.add_argument("--model", default="gpt-oss:20b-128k")
    parser.add_argument("--host", default="http://192.168.1.74:11434")
    parser.add_argument(
        "--case",
        help="Run only this test case name (default: all)",
    )
    args = parser.parse_args()

    cases = TEST_CASES
    if args.case:
        cases = [c for c in cases if c["name"] == args.case]
        if not cases:
            print(f"Unknown case: {args.case}", file=sys.stderr)
            print(
                f"Available: {', '.join(c['name'] for c in TEST_CASES)}",
                file=sys.stderr,
            )
            sys.exit(1)

    results = []
    for case in cases:
        try:
            r = run_test(case, model=args.model, host=args.host)
            results.append(r)
        except Exception as e:
            print(f"ERROR in {case['name']}: {e}", file=sys.stderr)
            results.append({"name": case["name"], "error": str(e)})

    # Summary table
    print(f"\n{'='*60}", file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(
        f"{'Case':<30} {'Lines':>5} {'Change':>6} {'Churn':>5} {'Status':>6}",
        file=sys.stderr,
    )
    print("-" * 60, file=sys.stderr)
    for r in results:
        if "error" in r:
            print(f"{r['name']:<30} {'ERROR':>5}", file=sys.stderr)
            continue
        status = (
            "PASS"
            if r["intended_change_made"] and r["unintended_churn"] == 0
            else "FAIL"
        )
        print(
            f"{r['name']:<30} {r['original_lines']:>5} "
            f"{'yes' if r['intended_change_made'] else 'NO':>6} "
            f"{r['unintended_churn']:>5} "
            f"{status:>6}",
            file=sys.stderr,
        )

    # JSON output
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
