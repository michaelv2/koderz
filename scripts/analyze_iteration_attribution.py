#!/usr/bin/env python3
"""
Analyze iteration attribution: checkpoint-driven vs self-recovery successes.

For each benchmark run, categorize every problem that needed >1 iteration into:
- "first_pass": solved on iteration 1 (spec alone was enough)
- "self_recovery": solved on iteration 2-4, 7-9, 12-14 (between checkpoints)
- "post_checkpoint": solved on iteration 5, 6, 10, 11, 15 (at or immediately after checkpoint)
- "failed": exhausted all iterations

Checkpoint interval is 5, so checkpoints fire at iterations 5, 10, 15.
Post-checkpoint iterations are 6, 11, 16 (first attempt after getting guidance).
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Study 1: Iteration sweep (9 runs)
STUDY1_RUNS = {
    "gpt-oss:20b-128k × 5 iter": "bench_e1cd2ab5_20260212_191726.json",
    "gpt-oss:20b-128k × 10 iter": "bench_faa1e88d_20260212_194600.json",
    "gpt-oss:20b-128k × 15 iter": "bench_4a439714_20260212_202118.json",
    "qwen3-coder:latest × 5 iter": "bench_23d9e9df_20260212_213319.json",
    "qwen3-coder:latest × 10 iter": "bench_b4111968_20260212_221118.json",
    "qwen3-coder:latest × 15 iter": "bench_9b5bfc3e_20260212_230043.json",
    "nemotron-3-nano:30b × 5 iter": "bench_b2e16b77_20260213_001451.json",
    "nemotron-3-nano:30b × 10 iter": "bench_76a06d1e_20260213_005325.json",
    "nemotron-3-nano:30b × 15 iter": "bench_c9da5402_20260213_013935.json",
}

# Study 2: Checkpoint model tier (3 runs) - all gpt-oss × 10 iter
STUDY2_RUNS = {
    "gpt-oss × gpt-5-nano CP": "bench_9d5ae700_20260213_092628.json",
    "gpt-oss × gpt-4.1-nano CP": "bench_212c9aca_20260213_095847.json",
    "gpt-oss × haiku CP": "bench_57a64320_20260213_102940.json",
}

CHECKPOINT_INTERVAL = 5

RESULTS_DIR = Path("/workspace/projects_safe/koderz/benchmark_results")


def classify_iteration(iteration, success, max_iterations):
    """Classify how a problem was solved based on iteration number."""
    if not success:
        return "failed"
    if iteration == 1:
        return "first_pass"

    # Checkpoints fire at multiples of checkpoint_interval (5, 10, 15)
    # The iteration immediately AFTER a checkpoint is the "post-checkpoint" attempt
    # because the model received guidance at the checkpoint
    checkpoint_iters = set()
    for cp in range(CHECKPOINT_INTERVAL, max_iterations + 1, CHECKPOINT_INTERVAL):
        # The checkpoint fires at iteration cp, guidance is available for iteration cp+1
        # But also: the model attempts iteration cp BEFORE the checkpoint fires
        # Actually - looking at the orchestrator code: checkpoint fires when
        # iteration % checkpoint_interval == 0, so at iterations 5, 10, 15.
        # The checkpoint guidance is then available for the NEXT iteration (6, 11, 16).
        checkpoint_iters.add(cp + 1)  # First iteration with checkpoint guidance

    if iteration in checkpoint_iters:
        return "post_checkpoint"

    # Check if this iteration is within 2 of a post-checkpoint iteration
    # (i.e., the model is still benefiting from recent checkpoint guidance)
    # Actually, let's be more precise: after a checkpoint, all subsequent iterations
    # until the next checkpoint have access to that guidance in the prompt.
    # So "post_checkpoint" should be any iteration after a checkpoint and before the next one
    # where the guidance was a factor.

    # Simpler: is there a checkpoint that fired before this iteration?
    prev_checkpoints = [cp for cp in range(CHECKPOINT_INTERVAL, iteration, CHECKPOINT_INTERVAL)]
    if prev_checkpoints:
        last_cp = max(prev_checkpoints)
        return "post_checkpoint_extended"  # Had checkpoint guidance available

    # Iterations 2-5 (before first checkpoint) = pure self-recovery from test feedback
    return "self_recovery"


def classify_iteration_strict(iteration, success, max_iterations):
    """
    Stricter classification:
    - first_pass: iteration 1
    - self_recovery: iterations 2-5 (before any checkpoint)
    - post_checkpoint: iterations 6-10, 11-15, etc. (after a checkpoint fired)
    - failed: didn't solve
    """
    if not success:
        return "failed"
    if iteration == 1:
        return "first_pass"
    if iteration <= CHECKPOINT_INTERVAL:
        return "self_recovery"
    return "post_checkpoint"


def analyze_run(run_name, filename):
    """Analyze a single benchmark run."""
    filepath = RESULTS_DIR / filename
    with open(filepath) as f:
        data = json.load(f)

    config = data["config"]
    max_iterations = config.get("max_iterations", 10)

    categories = defaultdict(list)
    multi_iter_problems = []

    for result in data["results"]:
        problem_id = result["problem_id"]
        success = result["success"]
        iterations = result["iterations"]

        cat = classify_iteration_strict(iterations, success, max_iterations)
        categories[cat].append({
            "problem_id": problem_id,
            "iterations": iterations,
        })

        if iterations > 1:
            multi_iter_problems.append({
                "problem_id": problem_id,
                "iterations": iterations,
                "success": success,
                "category": cat,
            })

    return {
        "run_name": run_name,
        "max_iterations": max_iterations,
        "total": len(data["results"]),
        "first_pass": len(categories["first_pass"]),
        "self_recovery": len(categories["self_recovery"]),
        "post_checkpoint": len(categories["post_checkpoint"]),
        "failed": len(categories["failed"]),
        "multi_iter_problems": multi_iter_problems,
        "categories": categories,
    }


def print_aggregate_table(all_results):
    """Print aggregate attribution table."""
    print("\n" + "=" * 100)
    print("AGGREGATE ITERATION ATTRIBUTION")
    print("=" * 100)
    print(f"\n{'Run':<40} {'Total':>5} {'Pass1':>6} {'Self':>6} {'Post-CP':>8} {'Fail':>6} {'Success':>8}")
    print("-" * 100)

    for r in all_results:
        total_success = r["first_pass"] + r["self_recovery"] + r["post_checkpoint"]
        print(f"{r['run_name']:<40} {r['total']:>5} {r['first_pass']:>6} "
              f"{r['self_recovery']:>6} {r['post_checkpoint']:>8} {r['failed']:>6} "
              f"{total_success:>5}/{r['total']}")


def print_multi_iter_details(all_results):
    """Print detailed info about problems needing >1 iteration."""
    print("\n" + "=" * 100)
    print("PROBLEMS REQUIRING >1 ITERATION (per run)")
    print("=" * 100)

    for r in all_results:
        if not r["multi_iter_problems"]:
            continue
        print(f"\n--- {r['run_name']} (max_iter={r['max_iterations']}) ---")
        for p in sorted(r["multi_iter_problems"], key=lambda x: x["iterations"]):
            status = "PASS" if p["success"] else "FAIL"
            cat = p["category"]
            # Add context about checkpoint proximity
            iters = p["iterations"]
            cp_note = ""
            if iters > 1:
                prev_cp = (iters - 1) // CHECKPOINT_INTERVAL * CHECKPOINT_INTERVAL
                if prev_cp > 0:
                    cp_note = f" (last CP at iter {prev_cp})"
                else:
                    cp_note = " (no CP yet)"
            print(f"  {p['problem_id']:<20} iter={iters:>2} {status:>4}  [{cat}]{cp_note}")


def cross_model_analysis(all_results):
    """Analyze patterns across models for the same problems."""
    print("\n" + "=" * 100)
    print("CROSS-MODEL ITERATION COMPARISON (Problems needing >1 iteration in any run)")
    print("=" * 100)

    # Collect all problems that needed >1 iter in any run
    problem_data = defaultdict(dict)
    for r in all_results:
        for p in r["multi_iter_problems"]:
            problem_data[p["problem_id"]][r["run_name"]] = {
                "iterations": p["iterations"],
                "success": p["success"],
                "category": p["category"],
            }
        # Also add first-pass problems for completeness
        for p in r["categories"]["first_pass"]:
            pid = p["problem_id"]
            if pid in problem_data:  # Only if it was multi-iter in another run
                problem_data[pid][r["run_name"]] = {
                    "iterations": 1,
                    "success": True,
                    "category": "first_pass",
                }

    for problem_id in sorted(problem_data.keys()):
        runs = problem_data[problem_id]
        if len(runs) < 2:
            continue
        print(f"\n  {problem_id}:")
        for run_name in sorted(runs.keys()):
            info = runs[run_name]
            status = "PASS" if info["success"] else "FAIL"
            print(f"    {run_name:<40} iter={info['iterations']:>2} {status} [{info['category']}]")


def checkpoint_vs_selfrecovery_summary(all_results):
    """
    The key question: among problems that ultimately succeed after >1 iteration,
    how many succeed BEFORE the first checkpoint vs AFTER?
    """
    print("\n" + "=" * 100)
    print("KEY QUESTION: SELF-RECOVERY vs CHECKPOINT-DRIVEN SUCCESS")
    print("(Among problems solved after >1 iteration)")
    print("=" * 100)

    # Group by model (aggregate across iteration configs)
    model_stats = defaultdict(lambda: {"self_recovery": 0, "post_checkpoint": 0,
                                        "self_recovery_problems": [], "post_checkpoint_problems": []})

    for r in all_results:
        model = r["run_name"].split(" × ")[0] if " × " in r["run_name"] else r["run_name"]
        for p in r["multi_iter_problems"]:
            if p["success"]:
                cat = p["category"]
                if cat == "self_recovery":
                    model_stats[model]["self_recovery"] += 1
                    model_stats[model]["self_recovery_problems"].append(
                        (p["problem_id"], p["iterations"], r["run_name"]))
                elif cat == "post_checkpoint":
                    model_stats[model]["post_checkpoint"] += 1
                    model_stats[model]["post_checkpoint_problems"].append(
                        (p["problem_id"], p["iterations"], r["run_name"]))

    for model in sorted(model_stats.keys()):
        stats = model_stats[model]
        total = stats["self_recovery"] + stats["post_checkpoint"]
        if total == 0:
            continue
        sr_pct = stats["self_recovery"] / total * 100 if total else 0
        pc_pct = stats["post_checkpoint"] / total * 100 if total else 0
        print(f"\n  {model}:")
        print(f"    Self-recovery (iter 2-5, before checkpoint): {stats['self_recovery']:>3} ({sr_pct:.0f}%)")
        for pid, iters, run in stats["self_recovery_problems"]:
            print(f"      {pid:<20} iter={iters} in {run}")
        print(f"    Post-checkpoint (iter 6+, after guidance):   {stats['post_checkpoint']:>3} ({pc_pct:.0f}%)")
        for pid, iters, run in stats["post_checkpoint_problems"]:
            print(f"      {pid:<20} iter={iters} in {run}")

    # Overall
    total_sr = sum(s["self_recovery"] for s in model_stats.values())
    total_pc = sum(s["post_checkpoint"] for s in model_stats.values())
    total = total_sr + total_pc
    print(f"\n  OVERALL (all models, all configs):")
    print(f"    Self-recovery:   {total_sr:>3} / {total} ({total_sr/total*100:.0f}%)")
    print(f"    Post-checkpoint: {total_pc:>3} / {total} ({total_pc/total*100:.0f}%)")


def iteration_distribution(all_results):
    """Show distribution of which specific iteration solved problems."""
    print("\n" + "=" * 100)
    print("ITERATION NUMBER DISTRIBUTION (successful problems only)")
    print("=" * 100)

    iter_counts = defaultdict(int)
    iter_details = defaultdict(list)

    for r in all_results:
        for cat_name in ["first_pass", "self_recovery", "post_checkpoint"]:
            for p in r["categories"][cat_name]:
                iters = p["iterations"]
                iter_counts[iters] += 1
                if iters > 1:
                    iter_details[iters].append((p["problem_id"], r["run_name"]))

    print(f"\n  {'Iteration':>10} {'Count':>6} {'Bar'}")
    print(f"  {'-'*10} {'-'*6} {'-'*50}")
    for i in sorted(iter_counts.keys()):
        bar = "#" * (iter_counts[i] // 5)
        marker = ""
        if i in [6, 11, 16]:
            marker = " <-- first iter after checkpoint"
        elif i in [5, 10, 15]:
            marker = " <-- checkpoint fires here"
        print(f"  {i:>10} {iter_counts[i]:>6} {bar}{marker}")

    # Show details for non-iter-1 successes
    print(f"\n  Details for iterations > 1:")
    for i in sorted(iter_details.keys()):
        print(f"\n  Iteration {i}:")
        for pid, run in iter_details[i]:
            print(f"    {pid:<20} ({run})")


def per_problem_deep_dive(all_results):
    """
    For each problem that was ever solved after >1 iteration,
    show the full picture across all runs.
    """
    print("\n" + "=" * 100)
    print("PER-PROBLEM DEEP DIVE: All problems ever needing >1 iteration")
    print("=" * 100)

    # Collect all data per problem
    problem_all_runs = defaultdict(list)
    for r in all_results:
        for result_item in r["categories"]["first_pass"]:
            problem_all_runs[result_item["problem_id"]].append({
                "run": r["run_name"],
                "iterations": 1,
                "success": True,
                "category": "first_pass",
                "max_iter": r["max_iterations"],
            })
        for result_item in r["categories"]["self_recovery"]:
            problem_all_runs[result_item["problem_id"]].append({
                "run": r["run_name"],
                "iterations": result_item["iterations"],
                "success": True,
                "category": "self_recovery",
                "max_iter": r["max_iterations"],
            })
        for result_item in r["categories"]["post_checkpoint"]:
            problem_all_runs[result_item["problem_id"]].append({
                "run": r["run_name"],
                "iterations": result_item["iterations"],
                "success": True,
                "category": "post_checkpoint",
                "max_iter": r["max_iterations"],
            })
        for result_item in r["categories"]["failed"]:
            problem_all_runs[result_item["problem_id"]].append({
                "run": r["run_name"],
                "iterations": result_item["iterations"],
                "success": False,
                "category": "failed",
                "max_iter": r["max_iterations"],
            })

    # Filter to problems that ever needed >1 iteration
    interesting = {}
    for pid, runs in problem_all_runs.items():
        if any(r["iterations"] > 1 for r in runs):
            interesting[pid] = runs

    for pid in sorted(interesting.keys()):
        runs = interesting[pid]
        print(f"\n  {pid}:")
        for r in sorted(runs, key=lambda x: x["run"]):
            status = "PASS" if r["success"] else "FAIL"
            print(f"    {r['run']:<45} iter={r['iterations']:>2}/{r['max_iter']:>2} {status} [{r['category']}]")


def main():
    all_runs = {}
    all_runs.update(STUDY1_RUNS)
    all_runs.update(STUDY2_RUNS)

    all_results = []
    for run_name, filename in all_runs.items():
        result = analyze_run(run_name, filename)
        all_results.append(result)

    # Sort by run name for consistent output
    all_results.sort(key=lambda x: x["run_name"])

    print_aggregate_table(all_results)
    checkpoint_vs_selfrecovery_summary(all_results)
    iteration_distribution(all_results)
    print_multi_iter_details(all_results)
    per_problem_deep_dive(all_results)
    cross_model_analysis(all_results)


if __name__ == "__main__":
    main()
