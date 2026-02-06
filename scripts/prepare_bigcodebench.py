#!/usr/bin/env python3
"""Download and prepare BigCodeBench dataset for koderz.

This script downloads BigCodeBench from HuggingFace and converts it to the
JSONL format expected by koderz. Use this to prepare the bigcodebench_hard.jsonl
file.

Usage:
    python scripts/prepare_bigcodebench.py --subset hard
    python scripts/prepare_bigcodebench.py --subset full
"""

import argparse
import json
from pathlib import Path


def download_bigcodebench(subset: str = "hard", output_dir: str = None):
    """Download BigCodeBench dataset and convert to JSONL.

    Args:
        subset: "hard" for BCB-Hard (148 tasks) or "full" for all 1,140 tasks
        output_dir: Output directory (defaults to koderz/data/)
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: 'datasets' package not installed.")
        print("Install with: pip install datasets")
        return False

    print(f"Downloading BigCodeBench ({subset} subset)...")

    # Load dataset from HuggingFace
    # The dataset is at bigcode/bigcodebench
    try:
        ds = load_dataset("bigcode/bigcodebench", split="v0.1.2")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("\nTrying alternative loading method...")
        try:
            # Try with trust_remote_code
            ds = load_dataset("bigcode/bigcodebench", split="v0.1.2", trust_remote_code=True)
        except Exception as e2:
            print(f"Error: {e2}")
            return False

    print(f"Loaded {len(ds)} total tasks")

    # Filter for Hard subset if requested
    if subset == "hard":
        # BCB-Hard task IDs are those with specific difficulty
        # The hard subset is typically indicated by a field or separate list
        # For now, let's check what fields are available
        print(f"Dataset features: {ds.features}")

        # Check if there's a difficulty field
        sample = ds[0]
        print(f"Sample task keys: {list(sample.keys())}")

        # BigCodeBench Hard subset is typically the first 148 tasks
        # or marked with a specific field. Let's check the task_id pattern
        hard_ids = set()

        # Try to find hard subset indicator
        for item in ds:
            task_id = item.get("task_id", "")
            # BCB-Hard uses specific task IDs - they start from BigCodeBench/0
            # The hard subset is documented as 148 tasks
            if "instruct_prompt" in item:
                # Has instruct prompt - this is the expected format
                hard_ids.add(task_id)

        print(f"Found {len(hard_ids)} tasks with instruct prompts")

        # If we can't identify hard subset, use first 148 tasks
        if len(hard_ids) > 148:
            print(f"Using first 148 tasks as BCB-Hard subset")
            task_ids = list(ds)[:148]
        else:
            task_ids = list(ds)
    else:
        task_ids = list(ds)

    # Determine output path
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "koderz" / "data"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if subset == "hard":
        output_file = output_dir / "bigcodebench_hard.jsonl"
    else:
        output_file = output_dir / "bigcodebench.jsonl"

    # Convert to JSONL format
    print(f"Writing to {output_file}...")
    count = 0

    with open(output_file, 'w') as f:
        for item in task_ids if subset != "hard" else task_ids[:148]:
            # Normalize to our expected format
            if isinstance(item, dict):
                record = item
            else:
                record = item

            # Handle libs field - it might be a string that needs parsing
            libs = record.get("libs", [])
            if isinstance(libs, str):
                try:
                    libs = json.loads(libs)
                except json.JSONDecodeError:
                    libs = [libs] if libs else []

            problem = {
                "task_id": record.get("task_id", f"BigCodeBench/{count}"),
                "complete_prompt": record.get("complete_prompt", record.get("prompt", "")),
                "instruct_prompt": record.get("instruct_prompt", ""),
                "entry_point": record.get("entry_point", ""),
                "test": record.get("test", ""),
                "canonical_solution": record.get("canonical_solution", record.get("solution", "")),
                "libs": libs,
            }

            # Also store prompt for compatibility with HumanEval interface
            problem["prompt"] = problem["complete_prompt"]

            f.write(json.dumps(problem) + "\n")
            count += 1

    print(f"Successfully wrote {count} tasks to {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download and prepare BigCodeBench dataset")
    parser.add_argument(
        "--subset",
        choices=["hard", "full"],
        default="hard",
        help="Which subset to download: 'hard' (148 tasks) or 'full' (1,140 tasks)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (defaults to koderz/data/)"
    )
    args = parser.parse_args()

    success = download_bigcodebench(args.subset, args.output_dir)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
