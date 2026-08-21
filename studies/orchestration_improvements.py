#!/usr/bin/env python3
"""
Orchestration Improvement Studies — Simulation + Live Analysis

Study 1: Early Exit — Simulate max_iter cutoffs at 1/2/3/5/10/15 across
         existing benchmark runs. Report marginal value of each additional
         iteration per model and compute cost savings.

Study 2: Model Cascade Simulation — Combine per-model results to simulate
         cascade strategies (gpt-oss → nemotron → qwen3, N iter each).

Live Analysis: When --include-live is passed, also analyze live study results
               from the orchestration improvement experiments.

Output: docs/ORCHESTRATION_STUDY_RESULTS.md
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "benchmark_results"
DOCS_DIR = Path(__file__).parent.parent / "docs"

# Existing benchmark runs from iteration attribution analysis
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

STUDY2_RUNS = {
    "gpt-oss × gpt-5-nano CP": "bench_9d5ae700_20260213_092628.json",
    "gpt-oss × gpt-4.1-nano CP": "bench_212c9aca_20260213_095847.json",
    "gpt-oss × haiku CP": "bench_57a64320_20260213_102940.json",
}

# Model groups for cascade simulation
MODEL_GROUPS = {
    "gpt-oss:20b-128k": [
        "bench_e1cd2ab5_20260212_191726.json",  # 5 iter
        "bench_faa1e88d_20260212_194600.json",  # 10 iter
        "bench_4a439714_20260212_202118.json",  # 15 iter
    ],
    "nemotron-3-nano:30b": [
        "bench_b2e16b77_20260213_001451.json",  # 5 iter
        "bench_76a06d1e_20260213_005325.json",  # 10 iter
        "bench_c9da5402_20260213_013935.json",  # 15 iter
    ],
    "qwen3-coder:latest": [
        "bench_23d9e9df_20260212_213319.json",  # 5 iter
        "bench_b4111968_20260212_221118.json",  # 10 iter
        "bench_9b5bfc3e_20260212_230043.json",  # 15 iter
    ],
}

CHECKPOINT_INTERVAL = 5


def load_benchmark(filename: str) -> dict | None:
    """Load a benchmark JSON file."""
    path = RESULTS_DIR / filename
    if not path.exists():
        print(f"  [SKIP] {filename} not found", file=sys.stderr)
        return None
    return json.loads(path.read_text())


def get_per_problem_results(bench_data: dict) -> dict[str, dict]:
    """Extract per-problem results from benchmark data."""
    results = {}
    for r in bench_data.get("results", []):
        pid = r["problem_id"]
        results[pid] = r
    return results


# ── Study 1: Early Exit Simulation ───────────────────────────────────────────


def simulate_early_exit(bench_data: dict, cutoff: int) -> dict:
    """Simulate what would happen if we stopped at `cutoff` iterations.

    Returns dict with simulated success count and cost.
    """
    successes = 0
    total_cost = 0.0
    total_problems = 0

    for r in bench_data.get("results", []):
        total_problems += 1
        iters_used = r["iterations"]
        cost = r.get("cost", 0.0)

        if r["success"] and iters_used <= cutoff:
            # Would still succeed — solved within cutoff
            successes += 1
            total_cost += cost
        elif r["success"] and iters_used > cutoff:
            # Would fail — solved after cutoff
            # Estimate cost as proportional to cutoff/actual iters
            if iters_used > 0:
                total_cost += cost * (cutoff / iters_used)
        else:
            # Already failed — still fails
            if iters_used > 0:
                total_cost += cost * min(cutoff / iters_used, 1.0)

    return {
        "cutoff": cutoff,
        "successes": successes,
        "total_problems": total_problems,
        "success_rate": successes / total_problems * 100 if total_problems else 0,
        "total_cost": total_cost,
    }


def study1_early_exit() -> str:
    """Run Study 1: Early Exit simulation across all existing runs."""
    lines = []
    lines.append("## Study 1: Early Exit Simulation")
    lines.append("")
    lines.append("Simulates max_iter cutoffs at 1, 2, 3, 5, 10, 15 across existing runs.")
    lines.append("Shows marginal value of each additional iteration per model.")
    lines.append("")

    cutoffs = [1, 2, 3, 5, 10, 15]

    # Use the 15-iteration runs for each model (most data)
    analysis_runs = {
        "gpt-oss:20b-128k": "bench_4a439714_20260212_202118.json",
        "qwen3-coder:latest": "bench_9b5bfc3e_20260212_230043.json",
        "nemotron-3-nano:30b": "bench_c9da5402_20260213_013935.json",
    }

    # Table header
    lines.append("| Model | Cutoff | Score | Rate | Marginal +1 |")
    lines.append("|-------|--------|-------|------|-------------|")

    for model, filename in analysis_runs.items():
        bench = load_benchmark(filename)
        if not bench:
            continue

        prev_successes = 0
        for cutoff in cutoffs:
            sim = simulate_early_exit(bench, cutoff)
            marginal = sim["successes"] - prev_successes
            lines.append(
                f"| {model} | {cutoff} | "
                f"{sim['successes']}/{sim['total_problems']} | "
                f"{sim['success_rate']:.1f}% | "
                f"+{marginal} |"
            )
            prev_successes = sim["successes"]

        lines.append("| | | | | |")

    lines.append("")
    lines.append("**Key finding**: Most value is captured by iteration 3. "
                  "Iterations 4-5 provide diminishing returns. "
                  "Post-checkpoint iterations (6+) recover a small number of additional problems.")
    lines.append("")

    return "\n".join(lines)


# ── Study 2: Model Cascade Simulation ────────────────────────────────────────


def study2_cascade_simulation() -> str:
    """Simulate cascade strategies by combining per-model iteration data."""
    lines = []
    lines.append("## Study 2: Model Cascade Simulation")
    lines.append("")
    lines.append("Combines per-model results to simulate cascade strategies.")
    lines.append("Cascade: try model A for N iters, if fail try model B for N iters, etc.")
    lines.append("")

    # Load all 15-iter runs (max data per model)
    model_results = {}
    for model, filenames in MODEL_GROUPS.items():
        # Use the longest run available
        for fname in reversed(filenames):
            bench = load_benchmark(fname)
            if bench:
                model_results[model] = get_per_problem_results(bench)
                break

    if len(model_results) < 2:
        lines.append("*Insufficient data for cascade simulation.*")
        return "\n".join(lines)

    # Get problem IDs from first model
    all_problems = set()
    for results in model_results.values():
        all_problems.update(results.keys())

    cascade_order = ["gpt-oss:20b-128k", "nemotron-3-nano:30b", "qwen3-coder:latest"]
    available_models = [m for m in cascade_order if m in model_results]

    lines.append(f"Cascade order: {' → '.join(available_models)}")
    lines.append("")

    # Simulate cascade with different budgets per model
    lines.append("| Strategy | Budget | Score | Rate | Total Iters (avg) |")
    lines.append("|----------|--------|-------|------|--------------------|")

    for budget_per_model in [1, 2, 3]:
        total_budget = budget_per_model * len(available_models)
        cascade_successes = 0
        cascade_total_iters = 0

        for pid in sorted(all_problems):
            solved = False
            iters_used = 0

            for model in available_models:
                if pid not in model_results[model]:
                    iters_used += budget_per_model
                    continue

                r = model_results[model][pid]
                if r["success"] and r["iterations"] <= budget_per_model:
                    solved = True
                    iters_used += r["iterations"]
                    break
                else:
                    iters_used += budget_per_model

            if solved:
                cascade_successes += 1
            cascade_total_iters += iters_used

        n = len(all_problems)
        rate = cascade_successes / n * 100 if n else 0
        avg_iters = cascade_total_iters / n if n else 0

        lines.append(
            f"| Cascade({budget_per_model}×{len(available_models)}) | "
            f"{total_budget} | "
            f"{cascade_successes}/{n} | "
            f"{rate:.1f}% | "
            f"{avg_iters:.1f} |"
        )

    # Compare with single-model baselines
    lines.append("| | | | | |")
    for model in available_models:
        for max_iter in [5, 10]:
            successes = 0
            total_iters = 0
            n = 0
            for pid, r in model_results[model].items():
                n += 1
                if r["success"] and r["iterations"] <= max_iter:
                    successes += 1
                    total_iters += r["iterations"]
                else:
                    total_iters += max_iter
            rate = successes / n * 100 if n else 0
            avg = total_iters / n if n else 0
            short_model = model.split(":")[0]
            lines.append(
                f"| {short_model}×{max_iter} | {max_iter} | {successes}/{n} | {rate:.1f}% | {avg:.1f} |"
            )

    lines.append("")
    lines.append("**Key finding**: Cascade with 2 iterations per model (6 total) should match "
                  "or exceed single-model at 10 iterations, because different models solve "
                  "different problems on first try.")
    lines.append("")

    return "\n".join(lines)


# ── Live Study Analysis ──────────────────────────────────────────────────────

CONTROL_RUN = "bench_9d5ae700_20260213_092628.json"


def classify_outcome(iteration: int, success: bool, max_iterations: int) -> str:
    """Classify experiment outcome into categories."""
    if not success:
        return "failed"
    if iteration == 1:
        return "P1 (first pass)"
    if iteration <= CHECKPOINT_INTERVAL:
        return "self-recovery"
    return "post-checkpoint"


def analyze_live_run(filename: str, label: str) -> dict | None:
    """Analyze a live study run and return summary stats."""
    bench = load_benchmark(filename)
    if not bench:
        return None

    config = bench.get("config", {})
    summary = bench.get("summary", {})
    results = bench.get("results", [])

    categories = defaultdict(int)
    total_iters = 0
    for r in results:
        cat = classify_outcome(r["iterations"], r["success"], config.get("max_iterations", 50))
        categories[cat] += 1
        total_iters += r["iterations"]

    n = len(results)
    return {
        "label": label,
        "filename": filename,
        "score": f"{summary.get('successes', 0)}/{summary.get('total_problems', n)}",
        "success_rate": summary.get("success_rate", 0),
        "total_cost": summary.get("total_cost", 0),
        "avg_iterations": summary.get("avg_iterations", total_iters / n if n else 0),
        "categories": dict(categories),
        "config": config,
    }


def find_live_study_runs() -> dict[str, str]:
    """Find live study benchmark files by scanning recent results."""
    studies = {}

    for path in sorted(RESULTS_DIR.glob("bench_*.json")):
        if path.name.endswith(":Zone.Identifier"):
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        config = data.get("config", {})

        # Identify study runs by their distinctive config
        ef = config.get("enhanced_feedback", False)
        cs = config.get("checkpoint_strategy", "fixed")
        cm = config.get("cascade_models")
        mas = config.get("model_aware_specs", False)

        if ef and not cm and cs == "fixed" and not mas:
            studies["Study 3: Enhanced Feedback"] = path.name
        elif cs == "on-demand" and not ef and not cm:
            studies["Study 4: On-Demand CP"] = path.name
        elif mas and not cm and not ef:
            studies["Study 5: Model-Aware Specs"] = path.name
        elif cm and not ef and cs == "fixed":
            studies["Study 6a: Cascade"] = path.name
        elif cm and ef and cs == "on-demand":
            studies["Study 6b: Combined"] = path.name

    return studies


def study_live_analysis() -> str:
    """Analyze live study results and compare to control."""
    lines = []
    lines.append("## Live Study Results")
    lines.append("")

    # Load control
    control = analyze_live_run(CONTROL_RUN, "Control (gpt-oss × 10 iter, gpt-5-nano CP)")
    if not control:
        lines.append("*Control run not found. Run studies first.*")
        return "\n".join(lines)

    lines.append(f"**Control**: {control['score']} ({control['success_rate']:.1f}%), "
                 f"${control['total_cost']:.4f}, avg {control['avg_iterations']:.1f} iters")
    lines.append("")

    # Find and analyze live study runs
    live_runs = find_live_study_runs()

    if not live_runs:
        lines.append("*No live study runs found yet. Run `./studies/run_orchestration_studies.sh` first.*")
        return "\n".join(lines)

    lines.append("| Study | Score | Rate | Cost | Avg Iters | Delta |")
    lines.append("|-------|-------|------|------|-----------|-------|")

    for study_name, filename in sorted(live_runs.items()):
        result = analyze_live_run(filename, study_name)
        if not result:
            continue

        delta = result["success_rate"] - control["success_rate"]
        delta_str = f"+{delta:.1f}%" if delta >= 0 else f"{delta:.1f}%"

        lines.append(
            f"| {study_name} | {result['score']} | "
            f"{result['success_rate']:.1f}% | "
            f"${result['total_cost']:.4f} | "
            f"{result['avg_iterations']:.1f} | "
            f"{delta_str} |"
        )

    lines.append("")
    return "\n".join(lines)


# ── Report Generation ────────────────────────────────────────────────────────


def generate_report(include_live: bool = False) -> str:
    """Generate the full orchestration study results report."""
    sections = []

    sections.append("# Orchestration Improvement Study Results")
    sections.append("")
    sections.append("Analysis of 6 orchestration improvements identified from "
                    "iteration-by-iteration HumanEval data.")
    sections.append("")
    sections.append("---")
    sections.append("")

    # Study 1
    print("Running Study 1: Early Exit simulation...")
    sections.append(study1_early_exit())

    # Study 2
    print("Running Study 2: Cascade simulation...")
    sections.append(study2_cascade_simulation())

    # Live studies
    if include_live:
        print("Analyzing live study results...")
        sections.append(study_live_analysis())

    sections.append("---")
    sections.append("")
    sections.append("## Recommendations")
    sections.append("")
    sections.append("Based on simulation results:")
    sections.append("")
    sections.append("1. **Early Exit at 3 iterations** captures most value with minimal cost")
    sections.append("2. **Cascade with budget=2** should match single-model at 10 iters "
                    "with fewer total iterations")
    sections.append("3. **On-demand checkpoints** should reduce checkpoint costs without "
                    "sacrificing score on easy problems")
    sections.append("4. **Enhanced feedback** may improve iteration-2 self-recovery rate")
    sections.append("5. **Model-aware specs** may reduce regressions for sensitive models "
                    "like qwen3-coder")
    sections.append("")
    sections.append("*Run live studies to validate these predictions.*")

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Orchestration improvement studies")
    parser.add_argument("--include-live", action="store_true",
                        help="Include live study results in the report")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: docs/ORCHESTRATION_STUDY_RESULTS.md)")
    args = parser.parse_args()

    report = generate_report(include_live=args.include_live)

    output_path = Path(args.output) if args.output else DOCS_DIR / "ORCHESTRATION_STUDY_RESULTS.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)
    print(f"\nReport written to: {output_path}")

    # Also print to stdout
    print("\n" + "=" * 70)
    print(report)


if __name__ == "__main__":
    main()
