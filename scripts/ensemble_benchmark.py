#!/usr/bin/env python3
"""Ensemble benchmark: simulate and validate local model ensemble strategies.

Study 3 from the Frontier-Guided Local Model Study.

Phase A (--simulate): Load existing zero-shot results, simulate ensemble strategies,
report per-strategy success rates without any new inference.

Phase B (--validate): Run actual ensemble on a fresh problem subset with a different
seed to confirm simulation accuracy.

Strategies:
  1. Sequential fallback: fixed order A→B→C, stop on first pass
  2. Run-all-and-check: run all models, take any that passes
  3. Oracle ceiling: upper bound (any model solves it)

Usage:
  python ensemble_benchmark.py --simulate
  python ensemble_benchmark.py --simulate --models gpt-oss:20b-128k qwen3-coder:latest nemotron-3-nano:30b
  python ensemble_benchmark.py --validate --problems 40 --seed 42
"""

import argparse
import json
import glob
import os
import sys
import subprocess
from itertools import permutations
from pathlib import Path

BENCHMARK_DIR = Path(__file__).parent / "benchmark_results"

# Default models and their preferred benchmark files
# Preference: no_spec=True, seed=23, temp=0.0, dataset=humaneval, 164 problems
DEFAULT_MODELS = ["gpt-oss:20b-128k", "qwen3-coder:latest", "nemotron-3-nano:30b"]


def load_benchmark_results(benchmark_dir: Path = BENCHMARK_DIR) -> list[dict]:
    """Load all benchmark result files."""
    results = []
    for f in sorted(glob.glob(str(benchmark_dir / "bench_*.json"))):
        with open(f) as fh:
            data = json.load(fh)
        data["_file"] = os.path.basename(f)
        results.append(data)
    return results


def find_best_run(
    all_runs: list[dict],
    model: str,
    dataset: str = "humaneval",
    mode: str = "zero-shot",
) -> dict | None:
    """Find the best comparable run for a model.

    Ranking priority:
      1. no_spec=True, seed=23, temp=0.0 (most controlled)
      2. no_spec=False, seed=23, temp=0.0
      3. Any seed/temp with no_spec=True
      4. Any run at all
    """
    candidates = []
    for run in all_runs:
        cfg = run.get("config", {})
        run_model = cfg.get("local_model", "")
        run_mode = cfg.get("mode", "") or run.get("mode", "")
        run_dataset = cfg.get("dataset", "") or "humaneval"
        n_problems = run.get("summary", {}).get("total_problems", 0)

        if run_model == model and run_mode == mode and run_dataset == dataset and n_problems == 164:
            no_spec = cfg.get("no_spec", False)
            seed = cfg.get("seed")
            temp = cfg.get("temperature")

            # Score: higher is better match
            score = 0
            if no_spec:
                score += 10
            if seed == 23:
                score += 5
            if temp == 0.0:
                score += 3

            candidates.append((score, run))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def extract_problem_results(run: dict) -> dict[str, bool]:
    """Extract problem_id → success mapping from a benchmark run."""
    return {r["problem_id"]: r["success"] for r in run.get("results", [])}


def simulate_sequential_fallback(
    model_results: dict[str, dict[str, bool]],
    model_order: list[str],
    problems: list[str],
) -> dict:
    """Simulate sequential fallback: try models in order, stop on first success.

    Returns dict with per-problem details and aggregate stats.
    """
    solved = 0
    total_model_runs = 0
    per_problem = {}

    for pid in problems:
        solved_by = None
        models_tried = 0
        for model in model_order:
            models_tried += 1
            if model_results[model].get(pid, False):
                solved_by = model
                break
        total_model_runs += models_tried
        per_problem[pid] = {
            "solved": solved_by is not None,
            "solved_by": solved_by,
            "models_tried": models_tried,
        }
        if solved_by is not None:
            solved += 1

    return {
        "strategy": "sequential_fallback",
        "model_order": model_order,
        "solved": solved,
        "total": len(problems),
        "success_rate": solved / len(problems) * 100 if problems else 0,
        "avg_models_per_problem": total_model_runs / len(problems) if problems else 0,
        "total_model_runs": total_model_runs,
        "per_problem": per_problem,
    }


def simulate_run_all(
    model_results: dict[str, dict[str, bool]],
    models: list[str],
    problems: list[str],
) -> dict:
    """Simulate run-all-and-check: run all models, succeed if any passes."""
    solved = 0
    per_problem = {}

    for pid in problems:
        solvers = [m for m in models if model_results[m].get(pid, False)]
        is_solved = len(solvers) > 0
        per_problem[pid] = {
            "solved": is_solved,
            "solved_by": solvers,
            "models_tried": len(models),
        }
        if is_solved:
            solved += 1

    return {
        "strategy": "run_all_and_check",
        "models": models,
        "solved": solved,
        "total": len(problems),
        "success_rate": solved / len(problems) * 100 if problems else 0,
        "avg_models_per_problem": len(models),
        "total_model_runs": len(models) * len(problems),
        "per_problem": per_problem,
    }


def analyze_complementarity(
    model_results: dict[str, dict[str, bool]],
    models: list[str],
    problems: list[str],
) -> dict:
    """Analyze which problems each model uniquely solves."""
    unique_solves = {}
    for model in models:
        unique = []
        for pid in problems:
            if model_results[model].get(pid, False):
                others_solve = any(
                    model_results[m].get(pid, False)
                    for m in models if m != model
                )
                if not others_solve:
                    unique.append(pid)
        unique_solves[model] = unique

    # Problems no model solves
    unsolvable = [
        pid for pid in problems
        if not any(model_results[m].get(pid, False) for m in models)
    ]

    # Problems all models solve
    all_solve = [
        pid for pid in problems
        if all(model_results[m].get(pid, False) for m in models)
    ]

    return {
        "unique_solves": unique_solves,
        "unsolvable": unsolvable,
        "all_solve": all_solve,
    }


def run_simulation(models: list[str], dataset: str = "humaneval", verbose: bool = False):
    """Run Phase A: ensemble simulation using existing benchmark data."""
    print(f"\n{'='*70}")
    print("  ENSEMBLE SIMULATION (Phase A)")
    print(f"  Models: {', '.join(models)}")
    print(f"  Dataset: {dataset}")
    print(f"{'='*70}\n")

    # Load all benchmark results
    all_runs = load_benchmark_results()
    print(f"Loaded {len(all_runs)} benchmark result files.\n")

    # Find best run for each model
    model_results = {}
    run_files = {}
    for model in models:
        run = find_best_run(all_runs, model, dataset=dataset)
        if run is None:
            print(f"ERROR: No zero-shot {dataset} results found for '{model}'")
            print("  Available models:")
            seen = set()
            for r in all_runs:
                m = r.get("config", {}).get("local_model", "")
                if m and m not in seen:
                    seen.add(m)
                    print(f"    - {m}")
            sys.exit(1)

        cfg = run.get("config", {})
        successes = run.get("summary", {}).get("successes", 0)
        sr = run.get("summary", {}).get("success_rate", 0)
        no_spec = cfg.get("no_spec", False)
        print(f"  {model:25s}  {successes}/164 ({sr:.1f}%)  no_spec={no_spec}  file={run['_file']}")
        model_results[model] = extract_problem_results(run)
        run_files[model] = run["_file"]

    # Get problem list from first model's results
    problems = sorted(model_results[models[0]].keys(), key=lambda x: int(x.split("/")[1]))
    print(f"\n  Total problems: {len(problems)}\n")

    # --- Individual model baselines ---
    print(f"{'─'*70}")
    print("  INDIVIDUAL MODEL BASELINES")
    print(f"{'─'*70}")
    print(f"  {'Model':25s} {'Solved':>8s} {'Rate':>8s} {'Cost':>10s}")
    print(f"  {'─'*25} {'─'*8} {'─'*8} {'─'*10}")
    for model in models:
        solved = sum(1 for pid in problems if model_results[model].get(pid, False))
        print(f"  {model:25s} {solved:>5d}/164 {solved/164*100:>7.1f}% {'$0.00':>10s}")

    # --- Oracle ceiling ---
    oracle_solved = sum(
        1 for pid in problems
        if any(model_results[m].get(pid, False) for m in models)
    )
    print(f"  {'─'*25} {'─'*8} {'─'*8} {'─'*10}")
    print(f"  {'Oracle (any model)':25s} {oracle_solved:>5d}/164 {oracle_solved/164*100:>7.1f}% {'$0.00':>10s}")

    # --- Complementarity analysis ---
    comp = analyze_complementarity(model_results, models, problems)
    print(f"\n{'─'*70}")
    print("  COMPLEMENTARITY ANALYSIS")
    print(f"{'─'*70}")
    for model in models:
        unique = comp["unique_solves"][model]
        print(f"  {model:25s}  uniquely solves: {len(unique):2d}  {unique if unique else '(none)'}")
    print(f"  {'All models solve':25s}  {len(comp['all_solve']):3d} problems")
    print(f"  {'No model solves':25s}  {len(comp['unsolvable']):3d} problems: {comp['unsolvable']}")

    # --- Sequential fallback (all permutations) ---
    print(f"\n{'─'*70}")
    print(f"  SEQUENTIAL FALLBACK (all {len(models)}! = {len(list(permutations(models)))} orderings)")
    print(f"{'─'*70}")
    print(f"  {'Order':50s} {'Solved':>8s} {'Rate':>8s} {'Avg Models':>12s}")
    print(f"  {'─'*50} {'─'*8} {'─'*8} {'─'*12}")

    fallback_results = []
    for perm in permutations(models):
        order = list(perm)
        result = simulate_sequential_fallback(model_results, order, problems)
        fallback_results.append(result)
        labels = [m.split(":")[0][:12] for m in order]
        order_str = " → ".join(labels)
        print(
            f"  {order_str:50s} {result['solved']:>5d}/164 "
            f"{result['success_rate']:>7.1f}% {result['avg_models_per_problem']:>10.2f}"
        )

    # Best fallback
    best_fb = max(fallback_results, key=lambda x: (x["solved"], -x["avg_models_per_problem"]))
    labels = [m.split(":")[0][:12] for m in best_fb["model_order"]]
    print(f"\n  Best ordering: {' → '.join(labels)}")
    print(f"    {best_fb['solved']}/164 ({best_fb['success_rate']:.1f}%), avg {best_fb['avg_models_per_problem']:.2f} models/problem")

    # --- Run-all-and-check ---
    run_all = simulate_run_all(model_results, models, problems)
    print(f"\n{'─'*70}")
    print("  RUN-ALL-AND-CHECK")
    print(f"{'─'*70}")
    print(f"  Solved: {run_all['solved']}/164 ({run_all['success_rate']:.1f}%)")
    print(f"  Models per problem: {run_all['avg_models_per_problem']:.0f} (always runs all)")
    print(f"  Total inference runs: {run_all['total_model_runs']}")

    # --- Summary comparison ---
    print(f"\n{'='*70}")
    print("  STRATEGY COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Strategy':35s} {'Solved':>8s} {'Rate':>8s} {'Avg Runs':>10s} {'API Cost':>10s}")
    print(f"  {'─'*35} {'─'*8} {'─'*8} {'─'*10} {'─'*10}")

    # Individual models
    for model in models:
        solved = sum(1 for pid in problems if model_results[model].get(pid, False))
        label = model.split(":")[0][:20] + " (solo)"
        print(f"  {label:35s} {solved:>5d}/164 {solved/164*100:>7.1f}% {'1.00':>10s} {'$0.00':>10s}")

    # Best sequential fallback
    labels = [m.split(":")[0][:8] for m in best_fb["model_order"]]
    fb_label = f"Fallback ({'>'.join(labels)})"
    print(
        f"  {fb_label:35s} {best_fb['solved']:>5d}/164 "
        f"{best_fb['success_rate']:>7.1f}% "
        f"{best_fb['avg_models_per_problem']:>10.2f} {'$0.00':>10s}"
    )

    # Run-all
    print(
        f"  {'Run-all-and-check':35s} {run_all['solved']:>5d}/164 "
        f"{run_all['success_rate']:>7.1f}% "
        f"{run_all['avg_models_per_problem']:>10.1f} {'$0.00':>10s}"
    )

    # Oracle
    print(f"  {'Oracle ceiling':35s} {oracle_solved:>5d}/164 {oracle_solved/164*100:>7.1f}% {'--':>10s} {'$0.00':>10s}")

    # gpt-5-nano reference
    print(f"  {'─'*35} {'─'*8} {'─'*8} {'─'*10} {'─'*10}")
    print(f"  {'gpt-5-nano (reference)':35s} {'161':>5s}/164 {'98.2':>7s}% {'1.00':>10s} {'$0.086':>10s}")

    # --- Unsolvable problem details ---
    if comp["unsolvable"] and verbose:
        print(f"\n{'─'*70}")
        print("  UNSOLVABLE PROBLEMS (no model solves)")
        print(f"{'─'*70}")
        for pid in comp["unsolvable"]:
            print(f"  {pid}")

    # --- Per-problem detail for failures (verbose) ---
    if verbose:
        print(f"\n{'─'*70}")
        print("  PER-PROBLEM FAILURE ANALYSIS")
        print(f"{'─'*70}")
        for pid in problems:
            solvers = [m for m in models if model_results[m].get(pid, False)]
            if len(solvers) < len(models):
                failed_by = [m.split(":")[0][:15] for m in models if not model_results[m].get(pid, False)]
                solved_by = [m.split(":")[0][:15] for m in solvers]
                print(f"  {pid:16s}  failed: {', '.join(failed_by):40s}  solved: {', '.join(solved_by)}")

    # --- Save results ---
    output = {
        "study": "ensemble_simulation",
        "models": models,
        "dataset": dataset,
        "run_files": run_files,
        "individual_baselines": {
            model: {
                "solved": sum(1 for pid in problems if model_results[model].get(pid, False)),
                "total": len(problems),
                "success_rate": sum(1 for pid in problems if model_results[model].get(pid, False)) / len(problems) * 100,
            }
            for model in models
        },
        "oracle_ceiling": {
            "solved": oracle_solved,
            "total": len(problems),
            "success_rate": oracle_solved / len(problems) * 100,
        },
        "best_sequential_fallback": {
            "model_order": best_fb["model_order"],
            "solved": best_fb["solved"],
            "success_rate": best_fb["success_rate"],
            "avg_models_per_problem": best_fb["avg_models_per_problem"],
        },
        "all_sequential_fallbacks": [
            {
                "model_order": r["model_order"],
                "solved": r["solved"],
                "success_rate": r["success_rate"],
                "avg_models_per_problem": r["avg_models_per_problem"],
            }
            for r in sorted(fallback_results, key=lambda x: (-x["solved"], x["avg_models_per_problem"]))
        ],
        "run_all_and_check": {
            "solved": run_all["solved"],
            "success_rate": run_all["success_rate"],
        },
        "complementarity": {
            "unique_solves": {m: comp["unique_solves"][m] for m in models},
            "unsolvable": comp["unsolvable"],
            "all_solve_count": len(comp["all_solve"]),
        },
        "per_problem": {
            pid: {model: model_results[model].get(pid, False) for model in models}
            for pid in problems
        },
    }

    out_path = BENCHMARK_DIR / "ensemble_simulation.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {out_path}")

    return output


def select_pilot_problems(
    model_results: dict[str, dict[str, bool]],
    models: list[str],
    baseline_file: str | None = None,
    n_total: int = 40,
    seed: int = 23,
) -> list[str]:
    """Select a curated pilot subset: all failures + random sample of successes.

    Priority:
      1. All problems where any model fails (the "hard" ones)
      2. Random sample from remaining to fill up to n_total
    """
    import random

    problems = sorted(model_results[models[0]].keys(), key=lambda x: int(x.split("/")[1]))

    # Find failure problems (any model fails)
    failures = [
        pid for pid in problems
        if not all(model_results[m].get(pid, False) for m in models)
    ]

    # If baseline file provided, also include baseline failures
    if baseline_file:
        try:
            with open(baseline_file) as f:
                baseline = json.load(f)
            baseline_failures = [
                r["problem_id"] for r in baseline.get("results", [])
                if not r.get("success", True)
            ]
            failures = list(set(failures + baseline_failures))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Sort failures by problem number
    failures.sort(key=lambda x: int(x.split("/")[1]))

    # Sample remaining from successes
    successes = [pid for pid in problems if pid not in failures]
    rng = random.Random(seed)
    n_sample = max(0, n_total - len(failures))
    sampled = sorted(rng.sample(successes, min(n_sample, len(successes))), key=lambda x: int(x.split("/")[1]))

    selected = failures + sampled
    print(f"  Pilot subset: {len(failures)} hard problems + {len(sampled)} sampled = {len(selected)} total")
    return selected


def run_validation(
    models: list[str],
    n_problems: int = 40,
    seed: int = 42,
    dataset: str = "humaneval",
):
    """Run Phase B: actual ensemble validation on fresh subset.

    Runs each model on the subset problems using the koderz CLI, then
    compares actual results to what simulation predicted.
    """
    print(f"\n{'='*70}")
    print("  ENSEMBLE VALIDATION (Phase B)")
    print(f"  Models: {', '.join(models)}")
    print(f"  Problems: {n_problems}, Seed: {seed}")
    print(f"{'='*70}\n")

    # First load existing results for pilot problem selection
    all_runs = load_benchmark_results()
    model_results = {}
    for model in models:
        run = find_best_run(all_runs, model, dataset=dataset)
        if run:
            model_results[model] = extract_problem_results(run)
        else:
            print(f"WARNING: No existing results for {model}, using empty")
            model_results[model] = {}

    # Select pilot problems
    pilot_problems = select_pilot_problems(model_results, models, n_total=n_problems, seed=seed)

    # Get problem indices
    problem_indices = [int(pid.split("/")[1]) for pid in pilot_problems]
    start = min(problem_indices)
    end = max(problem_indices) + 1

    # Build problem list for --problems flag (if CLI supports it)
    # Otherwise, we run full range and filter
    print(f"\n  Running {len(models)} models on {len(pilot_problems)} problems...")
    print(f"  Problem range: {start}-{end} (will filter to selected subset)")

    # Run each model
    validation_results = {}
    for model in models:
        print(f"\n  Running {model}...")
        cmd = [
            "poetry", "run", "koderz", "benchmark",
            "--start", str(start), "--end", str(end),
            "--local-model", model,
            "--mode", "zero-shot",
            "--no-spec",
            "--seed", str(seed),
            "--temperature", "0.0",
            "--dataset", dataset,
        ]
        print(f"  $ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:500]}")
            continue

        # Find the most recent benchmark file for this model
        latest = max(
            glob.glob(str(BENCHMARK_DIR / "bench_*.json")),
            key=os.path.getmtime,
        )
        with open(latest) as f:
            run_data = json.load(f)

        # Filter to pilot problems only
        pilot_results = {
            r["problem_id"]: r["success"]
            for r in run_data.get("results", [])
            if r["problem_id"] in pilot_problems
        }
        validation_results[model] = pilot_results
        solved = sum(1 for v in pilot_results.values() if v)
        print(f"  {model}: {solved}/{len(pilot_results)} on pilot subset")

    if not validation_results:
        print("\nERROR: No validation results collected.")
        return

    # Compare simulation predictions vs actual
    print(f"\n{'─'*70}")
    print("  SIMULATION vs ACTUAL COMPARISON")
    print(f"{'─'*70}")

    for model in models:
        if model not in validation_results:
            continue
        sim_results = model_results.get(model, {})
        actual_results = validation_results[model]

        matches = 0
        mismatches = 0
        for pid in pilot_problems:
            sim = sim_results.get(pid)
            actual = actual_results.get(pid)
            if sim is not None and actual is not None:
                if sim == actual:
                    matches += 1
                else:
                    mismatches += 1
                    print(f"  MISMATCH {pid}: sim={sim}, actual={actual} ({model})")

        total = matches + mismatches
        if total:
            print(f"  {model}: {matches}/{total} predictions matched ({matches/total*100:.1f}%)")

    # Run ensemble strategies on actual results
    print(f"\n{'─'*70}")
    print("  ENSEMBLE STRATEGIES ON VALIDATION DATA")
    print(f"{'─'*70}")

    run_all = simulate_run_all(validation_results, models, pilot_problems)
    print(f"  Run-all-and-check: {run_all['solved']}/{len(pilot_problems)} ({run_all['success_rate']:.1f}%)")

    best_fb = None
    for perm in permutations(models):
        order = list(perm)
        result = simulate_sequential_fallback(validation_results, order, pilot_problems)
        if best_fb is None or result["solved"] > best_fb["solved"]:
            best_fb = result
    if best_fb:
        labels = [m.split(":")[0][:12] for m in best_fb["model_order"]]
        print(f"  Best fallback ({' → '.join(labels)}): {best_fb['solved']}/{len(pilot_problems)} ({best_fb['success_rate']:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Ensemble benchmark: simulate and validate local model ensemble strategies"
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Phase A: simulate ensemble using existing benchmark data"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Phase B: run actual ensemble validation on fresh subset"
    )
    parser.add_argument(
        "--models", nargs="+", default=DEFAULT_MODELS,
        help=f"Models to include in ensemble (default: {' '.join(DEFAULT_MODELS)})"
    )
    parser.add_argument(
        "--dataset", default="humaneval",
        help="Dataset to use (default: humaneval)"
    )
    parser.add_argument(
        "--problems", type=int, default=40,
        help="Number of problems for validation subset (default: 40)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for validation (default: 42)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show per-problem failure details"
    )

    args = parser.parse_args()

    if not args.simulate and not args.validate:
        parser.print_help()
        print("\nSpecify --simulate and/or --validate")
        sys.exit(1)

    if args.simulate:
        run_simulation(args.models, dataset=args.dataset, verbose=args.verbose)

    if args.validate:
        run_validation(args.models, n_problems=args.problems, seed=args.seed, dataset=args.dataset)


if __name__ == "__main__":
    main()
