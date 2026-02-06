"""CLI interface for koderz."""

import os
import asyncio
import click
import uuid
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from .orchestrator import ExperimentOrchestrator
from .cortex.client import CortexClient
from .models.factory import ModelFactory
from .models.registry import get_tier
from .benchmarks.humaneval import HumanEval, DATASET_FILES as HUMANEVAL_DATASET_FILES
from .benchmarks.bigcodebench import BigCodeBench, DATASET_FILES as BCB_DATASET_FILES
from .analysis.frontier_costs import FrontierCostRegistry


# Load environment variables
load_dotenv()


def _build_result_entry(r: dict) -> dict:
    """Build a per-experiment result entry for benchmark JSON output."""
    ca = r["cost_analysis"]
    entry = {
        "experiment_id": r["experiment_id"],
        "problem_id": r["problem_id"],
        "success": r["success"],
        "iterations": r["iterations"],
        "cost": ca["actual_cost"],
    }
    # Include token usage if available
    total_in = ca.get("total_input_tokens", 0)
    total_out = ca.get("total_output_tokens", 0)
    if total_in or total_out:
        entry["usage"] = {
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": ca.get("total_cache_read_tokens", 0),
            "cache_creation_tokens": ca.get("total_cache_creation_tokens", 0),
        }
    return entry


def _aggregate_token_usage(results: list[dict]) -> dict:
    """Aggregate token usage across a list of experiment results."""
    total_in = 0
    total_out = 0
    total_cache_read = 0
    total_cache_create = 0
    for r in results:
        ca = r["cost_analysis"]
        total_in += ca.get("total_input_tokens", 0)
        total_out += ca.get("total_output_tokens", 0)
        total_cache_read += ca.get("total_cache_read_tokens", 0)
        total_cache_create += ca.get("total_cache_creation_tokens", 0)
    if not total_in and not total_out:
        return {}
    usage = {
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
    }
    if total_cache_read or total_cache_create:
        usage["total_cache_read_tokens"] = total_cache_read
        usage["total_cache_creation_tokens"] = total_cache_create
    return usage

# Default isolated database for koderz experiment data
DEFAULT_CORTEX_DB = os.path.expanduser("~/.claude-cortex/koderz.db")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Koderz: Multi-model swarm experiment framework.

    Run coding experiments using local models supervised by frontier models,
    with all data tracked via claude-cortex-core MCP server.
    """
    pass


@cli.command()
@click.option(
    "--problem-id",
    required=True,
    help="HumanEval problem ID (e.g., HumanEval/0)"
)
@click.option(
    "--local-model",
    default="codellama:70b",
    help="Local model to use for iterations"
)
@click.option(
    "--frontier-spec-model",
    default="gpt-oss:20b",
    help="Model for spec generation (default: gpt-oss:20b - validated 100% first-try success)"
)
@click.option(
    "--frontier-checkpoint-model",
    default="claude-sonnet-4-5",
    help="Frontier model for checkpoints"
)
@click.option(
    "--max-iterations",
    default=50,
    type=int,
    help="Maximum iterations before giving up"
)
@click.option(
    "--checkpoint-interval",
    default=5,
    type=int,
    help="Checkpoint every N iterations"
)
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js (defaults to CORTEX_PATH env var)"
)
@click.option(
    "--cortex-db",
    default=None,
    help="Path to cortex database file (defaults to CORTEX_DB env var or ~/.claude-cortex/koderz.db)"
)
@click.option(
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
@click.option(
    "--reuse-spec",
    is_flag=True,
    help="Reuse existing spec from Cortex instead of regenerating"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode: save all iteration outputs and checkpoint guidance"
)
@click.option(
    "--debug-dir",
    default="./debug",
    help="Directory to save debug outputs (default: ./debug)"
)
@click.option(
    "--mode",
    type=click.Choice(["zero-shot", "iterative"], case_sensitive=False),
    default="iterative",
    help="Evaluation mode: zero-shot (single attempt, no feedback) or iterative (with test feedback)"
)
@click.option(
    "--timeout",
    default=300,
    type=int,
    help="Request timeout in seconds for Ollama (default: 300)"
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum retry attempts for Ollama timeouts/overload (default: 3)"
)
@click.option(
    "--num-ctx",
    default=5120,
    type=int,
    help="Context window size for Ollama models in tokens (default: 5120, tuned from real data)"
)
@click.option(
    "--seed",
    default=None,
    type=int,
    help="Random seed for Ollama (set for reproducible output)"
)
@click.option(
    "--temperature",
    default=0.1,
    type=float,
    help="Temperature for Ollama sampling (default: 0.1)"
)
@click.option(
    "--no-spec",
    is_flag=True,
    help="Skip spec generation entirely (isolate spec contribution)"
)
@click.option(
    "--no-checkpoints",
    is_flag=True,
    help="Disable checkpoint reviews (isolate checkpoint contribution)"
)
@click.option(
    "--no-cot",
    is_flag=True,
    help="Disable chain-of-thought reasoning in prompts (code only output)"
)
@click.option(
    "--dataset",
    type=click.Choice(["humaneval", "humaneval+", "bigcodebench", "bigcodebench-hard"], case_sensitive=False),
    default="humaneval",
    help="Dataset: humaneval, humaneval+, bigcodebench (1140 tasks), or bigcodebench-hard (148 tasks)"
)
@click.option(
    "--test-timeout",
    default=None,
    type=int,
    help="Timeout in seconds for test execution per iteration (default: 10 for HumanEval, 30 for BigCodeBench)"
)
def run(
    problem_id,
    local_model,
    frontier_spec_model,
    frontier_checkpoint_model,
    max_iterations,
    checkpoint_interval,
    cortex_path,
    cortex_db,
    humaneval_path,
    reuse_spec,
    debug,
    debug_dir,
    mode,
    timeout,
    max_retries,
    num_ctx,
    seed,
    temperature,
    no_spec,
    no_checkpoints,
    no_cot,
    dataset,
    test_timeout
):
    """Run a single experiment on a HumanEval or BigCodeBench problem."""

    # Validate environment
    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path:
        click.echo("Error: CORTEX_PATH not set", err=True)
        click.echo("Set via --cortex-path or CORTEX_PATH env var", err=True)
        return 1

    if not Path(cortex_path).exists():
        click.echo(f"Error: Cortex path not found: {cortex_path}", err=True)
        return 1

    cortex_db = cortex_db or os.getenv("CORTEX_DB", DEFAULT_CORTEX_DB)

    # Determine if using BigCodeBench
    is_bigcodebench = dataset.lower().startswith("bigcodebench")

    # Set default test timeout based on dataset
    if test_timeout is None:
        test_timeout = 30 if is_bigcodebench else 10

    # Initialize clients
    click.echo("Initializing clients...")
    model_factory = ModelFactory(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
        num_ctx=num_ctx,
        seed=seed,
        temperature=temperature
    )

    # Load dataset
    click.echo(f"Loading {dataset} dataset...")
    if is_bigcodebench:
        benchmark = BigCodeBench(data_path=humaneval_path, dataset=dataset)
        download_cmd = f"koderz download-data --dataset {dataset}"
    else:
        benchmark = HumanEval(data_path=humaneval_path, dataset=dataset)
        download_cmd = "koderz download-data --dataset humaneval+"

    if benchmark.count() == 0:
        click.echo(f"Error: No problems found for dataset '{dataset}'.", err=True)
        click.echo(f"Download it with: {download_cmd}", err=True)
        return 1

    try:
        problem = benchmark.get_problem(problem_id)
    except KeyError:
        click.echo(f"Error: Problem ID not found: {problem_id}", err=True)
        click.echo(f"Available problems: {benchmark.count()}", err=True)
        return 1

    # Run experiment (using one-shot Cortex sessions for now to avoid blocking issues)
    cortex = CortexClient(cortex_path, db_path=cortex_db)
    orchestrator = ExperimentOrchestrator(
        cortex=cortex,
        model_factory=model_factory,
        checkpoint_interval=checkpoint_interval,
        debug=debug,
        debug_dir=debug_dir,
        test_timeout=test_timeout,
        dataset_type="bigcodebench" if is_bigcodebench else "humaneval"
    )

    result = asyncio.run(
        orchestrator.run_experiment(
            problem=problem,
            max_iterations=max_iterations,
            local_model=local_model,
            frontier_spec_model=frontier_spec_model,
            frontier_checkpoint_model=frontier_checkpoint_model,
            reuse_spec=reuse_spec,
            mode=mode,
            no_spec=no_spec,
            no_checkpoints=no_checkpoints,
            no_cot=no_cot
        )
    )

    # Exit with success/failure code
    return 0 if result["success"] else 1


@cli.command()
@click.option(
    "--start",
    default=0,
    type=int,
    help="Start index (inclusive)"
)
@click.option(
    "--end",
    default=10,
    type=int,
    help="End index (exclusive)"
)
@click.option(
    "--local-model",
    default="codellama:70b",
    help="Local model to use"
)
@click.option(
    "--max-iterations",
    default=50,
    type=int,
    help="Max iterations per problem"
)
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js"
)
@click.option(
    "--cortex-db",
    default=None,
    help="Path to cortex database file (defaults to CORTEX_DB env var or ~/.claude-cortex/koderz.db)"
)
@click.option(
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
@click.option(
    "--mode",
    type=click.Choice(["zero-shot", "iterative", "comparative"], case_sensitive=False),
    default="iterative",
    help="Evaluation mode: zero-shot, iterative, or comparative (runs both and compares)"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode: save all iteration outputs and checkpoint guidance"
)
@click.option(
    "--debug-dir",
    default="./debug",
    help="Directory to save debug outputs (default: ./debug)"
)
@click.option(
    "--timeout",
    default=300,
    type=int,
    help="Request timeout in seconds for Ollama (default: 300)"
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum retry attempts for Ollama timeouts/overload (default: 3)"
)
@click.option(
    "--num-ctx",
    default=5120,
    type=int,
    help="Context window size for Ollama models in tokens (default: 5120, tuned from real data)"
)
@click.option(
    "--seed",
    default=None,
    type=int,
    help="Random seed for Ollama (set for reproducible output)"
)
@click.option(
    "--temperature",
    default=0.1,
    type=float,
    help="Temperature for Ollama sampling (default: 0.1)"
)
@click.option(
    "--no-spec",
    is_flag=True,
    help="Skip spec generation entirely (isolate spec contribution)"
)
@click.option(
    "--no-checkpoints",
    is_flag=True,
    help="Disable checkpoint reviews (isolate checkpoint contribution)"
)
@click.option(
    "--no-cot",
    is_flag=True,
    help="Disable chain-of-thought reasoning in prompts (code only output)"
)
@click.option(
    "--dataset",
    type=click.Choice(["humaneval", "humaneval+", "bigcodebench", "bigcodebench-hard"], case_sensitive=False),
    default="humaneval",
    help="Dataset: humaneval, humaneval+, bigcodebench (1140 tasks), or bigcodebench-hard (148 tasks)"
)
@click.option(
    "--test-timeout",
    default=None,
    type=int,
    help="Timeout in seconds for test execution per iteration (default: 10 for HumanEval, 30 for BigCodeBench)"
)
@click.option(
    "--baseline-model",
    default=None,
    type=str,
    help="Frontier model to compare costs against (e.g., gpt-5-mini). Uses recorded costs from frontier_costs.json"
)
def benchmark(start, end, local_model, max_iterations, cortex_path, cortex_db, humaneval_path, mode, debug, debug_dir, timeout, max_retries, num_ctx, seed, temperature, no_spec, no_checkpoints, no_cot, dataset, test_timeout, baseline_model):
    """Run benchmark on a range of HumanEval or BigCodeBench problems.

    \b
    Modes:
      - zero-shot: Single attempt per problem, no test feedback
      - iterative: Multiple attempts with test feedback (default)
      - comparative: Run both modes and compare results
    """

    # Validate environment
    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        return 1

    cortex_db = cortex_db or os.getenv("CORTEX_DB", DEFAULT_CORTEX_DB)

    # Determine if using BigCodeBench
    is_bigcodebench = dataset.lower().startswith("bigcodebench")

    # Set default test timeout based on dataset
    if test_timeout is None:
        test_timeout = 30 if is_bigcodebench else 10

    # Initialize clients
    cortex = CortexClient(cortex_path, db_path=cortex_db)
    model_factory = ModelFactory(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
        num_ctx=num_ctx,
        seed=seed,
        temperature=temperature
    )

    # Initialize frontier cost registry
    cost_registry = FrontierCostRegistry()
    model_tier = get_tier(local_model)
    is_frontier_model = model_tier in ("small_frontier", "frontier")

    if is_frontier_model:
        click.echo(f"Note: Recording costs for frontier model '{local_model}' to frontier_costs.json")

    if baseline_model:
        baseline_summary = cost_registry.get_model_summary(baseline_model, dataset=dataset)
        if baseline_summary["problem_count"] == 0:
            click.echo(f"Warning: No recorded costs for baseline model '{baseline_model}' (dataset={dataset})")
            click.echo("Run a benchmark with that model first to record costs, or omit --baseline-model")
        else:
            click.echo(f"Baseline: {baseline_model} ({baseline_summary['problem_count']} problems, ${baseline_summary['total_median_cost']:.4f} total)")

    # Load dataset
    if is_bigcodebench:
        benchmark_loader = BigCodeBench(data_path=humaneval_path, dataset=dataset)
        download_cmd = f"koderz download-data --dataset {dataset}"
    else:
        benchmark_loader = HumanEval(data_path=humaneval_path, dataset=dataset)
        download_cmd = "koderz download-data --dataset humaneval+"

    if benchmark_loader.count() == 0:
        click.echo(f"Error: No problems found for dataset '{dataset}'.", err=True)
        click.echo(f"Download it with: {download_cmd}", err=True)
        return 1

    problem_ids = benchmark_loader.list_problems()[start:end]

    if mode == "comparative":
        # Generate benchmark run ID
        benchmark_run_id = f"bench_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        # Run comparative benchmark (both modes on same problems)
        click.echo(f"\nRunning COMPARATIVE benchmark on {len(problem_ids)} problems...")
        click.echo(f"Benchmark Run ID: {benchmark_run_id}")
        click.echo(f"Range: {start} to {end}")
        click.echo(f"Local model: {local_model}")
        click.echo(f"Testing both zero-shot and iterative modes\n")

        zero_shot_results = []
        iterative_results = []

        for i, problem_id in enumerate(problem_ids, 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"Problem {i}/{len(problem_ids)}: {problem_id}")
            click.echo(f"{'='*60}")

            problem = benchmark_loader.get_problem(problem_id)

            # Run zero-shot
            click.echo("\n[ZERO-SHOT MODE]")
            orchestrator_zs = ExperimentOrchestrator(
                cortex=cortex,
                model_factory=model_factory,
                debug=debug,
                debug_dir=debug_dir,
                test_timeout=test_timeout,
                dataset_type="bigcodebench" if is_bigcodebench else "humaneval"
            )
            result_zs = asyncio.run(
                orchestrator_zs.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode="zero-shot",
                    benchmark_run_id=benchmark_run_id,
                    no_spec=no_spec,
                    no_checkpoints=no_checkpoints,
                    no_cot=no_cot
                )
            )
            zero_shot_results.append(result_zs)
            zs_status = "✓ PASS" if result_zs["success"] else "✗ FAIL"
            click.echo(f"  {zs_status} | Cost: ${result_zs['cost_analysis']['actual_cost']:.4f}")

            # Run iterative
            click.echo("\n[ITERATIVE MODE]")
            orchestrator_iter = ExperimentOrchestrator(
                cortex=cortex,
                model_factory=model_factory,
                debug=debug,
                debug_dir=debug_dir,
                test_timeout=test_timeout,
                dataset_type="bigcodebench" if is_bigcodebench else "humaneval"
            )
            result_iter = asyncio.run(
                orchestrator_iter.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode="iterative",
                    benchmark_run_id=benchmark_run_id,
                    no_spec=no_spec,
                    no_checkpoints=no_checkpoints,
                    no_cot=no_cot
                )
            )
            iterative_results.append(result_iter)
            iter_status = "✓ PASS" if result_iter["success"] else "✗ FAIL"
            click.echo(f"  {iter_status} | Cost: ${result_iter['cost_analysis']['actual_cost']:.4f} | Iterations: {result_iter['iterations']}")

            # Record frontier model costs to registry (use zero-shot as baseline)
            if is_frontier_model:
                ca = result_zs["cost_analysis"]
                cost_registry.record(
                    model=local_model,
                    problem_id=problem_id,
                    cost=ca["actual_cost"],
                    input_tokens=ca.get("total_input_tokens", 0),
                    output_tokens=ca.get("total_output_tokens", 0),
                    cache_read_tokens=ca.get("total_cache_read_tokens", 0),
                    cache_creation_tokens=ca.get("total_cache_creation_tokens", 0),
                    dataset=dataset,
                    temperature=temperature,
                    seed=seed,
                    success=result_zs["success"],
                )

        # Calculate statistics
        zs_successes = sum(1 for r in zero_shot_results if r["success"])
        iter_successes = sum(1 for r in iterative_results if r["success"])

        zs_total_cost = sum(r["cost_analysis"]["actual_cost"] for r in zero_shot_results)
        iter_total_cost = sum(r["cost_analysis"]["actual_cost"] for r in iterative_results)

        zs_avg_cost = zs_total_cost / len(zero_shot_results) if zero_shot_results else 0
        iter_avg_cost = iter_total_cost / len(iterative_results) if iterative_results else 0

        zs_avg_iters = sum(r["iterations"] for r in zero_shot_results) / len(zero_shot_results) if zero_shot_results else 0
        iter_avg_iters = sum(r["iterations"] for r in iterative_results) / len(iterative_results) if iterative_results else 0

        zs_success_rate = zs_successes / len(zero_shot_results) * 100 if zero_shot_results else 0
        iter_success_rate = iter_successes / len(iterative_results) * 100 if iterative_results else 0

        # Print comparative results
        click.echo(f"\n{'='*70}")
        click.echo("COMPARATIVE BENCHMARK RESULTS")
        click.echo(f"{'='*70}")
        click.echo(f"\n{'Mode':<15} | {'Success Rate':<15} | {'Avg Cost':<12} | {'Avg Iterations':<15}")
        click.echo(f"{'-'*15}-+-{'-'*15}-+-{'-'*12}-+-{'-'*15}")
        click.echo(f"{'Zero-Shot':<15} | {zs_success_rate:>5.1f}% ({zs_successes:>2}/{len(zero_shot_results):<2}) | ${zs_avg_cost:>10.4f} | {zs_avg_iters:>14.1f}")
        click.echo(f"{'Iterative':<15} | {iter_success_rate:>5.1f}% ({iter_successes:>2}/{len(iterative_results):<2}) | ${iter_avg_cost:>10.4f} | {iter_avg_iters:>14.1f}")
        click.echo(f"{'-'*15}-+-{'-'*15}-+-{'-'*12}-+-{'-'*15}")

        # Calculate improvements
        success_improvement = iter_success_rate - zs_success_rate
        cost_diff = iter_avg_cost - zs_avg_cost
        iter_diff = iter_avg_iters - zs_avg_iters

        improvement_symbol = "+" if success_improvement > 0 else ""
        click.echo(f"{'Improvement':<15} | {improvement_symbol}{success_improvement:>5.1f}% points  | ${cost_diff:>+10.4f} | {iter_diff:>+14.1f}")

        click.echo(f"\n{'='*70}")
        click.echo("SUMMARY")
        click.echo(f"{'='*70}")
        click.echo(f"Total problems tested: {len(problem_ids)}")
        click.echo(f"Zero-shot total cost: ${zs_total_cost:.4f}")
        click.echo(f"Iterative total cost: ${iter_total_cost:.4f}")
        click.echo(f"Combined total cost: ${zs_total_cost + iter_total_cost:.4f}")

        if success_improvement > 0:
            click.echo(f"\n✓ Iteration improves success rate by {success_improvement:.1f} percentage points")
        elif success_improvement < 0:
            click.echo(f"\n✗ Iteration decreases success rate by {abs(success_improvement):.1f} percentage points")
        else:
            click.echo(f"\n= No change in success rate between modes")

        # Store benchmark summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "run_id": benchmark_run_id,
            "mode": "comparative",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "config": {
                "local_model": local_model,
                "problem_range": f"{start}-{end}",
                "problems": problem_ids,
                "max_iterations": max_iterations,
                "no_spec": no_spec,
                "no_checkpoints": no_checkpoints,
                "no_cot": no_cot,
                "dataset": dataset,
                "temperature": temperature,
                "seed": seed
            },
            "zero_shot": {
                "results": [_build_result_entry(r) for r in zero_shot_results],
                "summary": {
                    "total_problems": len(zero_shot_results),
                    "successes": zs_successes,
                    "success_rate": zs_success_rate,
                    "total_cost": zs_total_cost,
                    "avg_cost": zs_avg_cost,
                    "avg_iterations": zs_avg_iters,
                    **_aggregate_token_usage(zero_shot_results)
                }
            },
            "iterative": {
                "results": [_build_result_entry(r) for r in iterative_results],
                "summary": {
                    "total_problems": len(iterative_results),
                    "successes": iter_successes,
                    "success_rate": iter_success_rate,
                    "total_cost": iter_total_cost,
                    "avg_cost": iter_avg_cost,
                    "avg_iterations": iter_avg_iters,
                    **_aggregate_token_usage(iterative_results)
                }
            },
            "comparison": {
                "success_rate_improvement": success_improvement,
                "cost_difference": cost_diff,
                "iteration_difference": iter_diff
            }
        }

        # Store in Cortex
        try:
            asyncio.run(cortex.remember(
                title=f"Benchmark Run {benchmark_run_id}",
                content=json.dumps(summary, indent=2),
                category="architecture",
                tags=["benchmark_run", benchmark_run_id, "comparative", local_model],
                importance="critical",
                metadata=summary
            ))
            cortex_stored = True
        except Exception as e:
            click.echo(f"Warning: Failed to store in Cortex: {e}", err=True)
            cortex_stored = False

        # Save to file
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        results_file = results_dir / f"{benchmark_run_id}.json"
        results_file.write_text(json.dumps(summary, indent=2))

        click.echo(f"\n{'='*70}")
        click.echo("BENCHMARK SUMMARY SAVED")
        click.echo(f"{'='*70}")
        if cortex_stored:
            click.echo(f"Cortex: tags=['benchmark_run', '{benchmark_run_id}']")
        else:
            click.echo("Cortex: FAILED (see warning above)")
        click.echo(f"File: {results_file}")

        return 0

    else:
        # Generate benchmark run ID
        benchmark_run_id = f"bench_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        # Run single-mode benchmark
        click.echo(f"\nRunning benchmark on {len(problem_ids)} problems...")
        click.echo(f"Benchmark Run ID: {benchmark_run_id}")
        click.echo(f"Range: {start} to {end}")
        click.echo(f"Local model: {local_model}")
        click.echo(f"Mode: {mode}\n")

        # Track aggregate stats
        results = []
        successes = 0
        total_cost = 0.0
        total_iterations = 0

        for i, problem_id in enumerate(problem_ids, 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"Problem {i}/{len(problem_ids)}: {problem_id}")
            click.echo(f"{'='*60}")

            problem = benchmark_loader.get_problem(problem_id)

            orchestrator = ExperimentOrchestrator(
                cortex=cortex,
                model_factory=model_factory,
                debug=debug,
                debug_dir=debug_dir,
                test_timeout=test_timeout,
                dataset_type="bigcodebench" if is_bigcodebench else "humaneval"
            )

            result = asyncio.run(
                orchestrator.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode=mode,
                    benchmark_run_id=benchmark_run_id,
                    no_spec=no_spec,
                    no_checkpoints=no_checkpoints,
                    no_cot=no_cot
                )
            )

            results.append(result)
            if result["success"]:
                successes += 1

            total_cost += result["cost_analysis"]["actual_cost"]
            total_iterations += result["iterations"]

            # Record frontier model costs to registry
            if is_frontier_model:
                ca = result["cost_analysis"]
                cost_registry.record(
                    model=local_model,
                    problem_id=problem_id,
                    cost=ca["actual_cost"],
                    input_tokens=ca.get("total_input_tokens", 0),
                    output_tokens=ca.get("total_output_tokens", 0),
                    cache_read_tokens=ca.get("total_cache_read_tokens", 0),
                    cache_creation_tokens=ca.get("total_cache_creation_tokens", 0),
                    dataset=dataset,
                    temperature=temperature,
                    seed=seed,
                    success=result["success"],
                )

        # Print aggregate results
        click.echo(f"\n{'='*60}")
        click.echo("BENCHMARK COMPLETE")
        click.echo(f"{'='*60}")
        click.echo(f"Mode: {mode}")
        click.echo(f"Problems: {len(problem_ids)}")
        click.echo(f"Successes: {successes} ({successes/len(problem_ids)*100:.1f}%)")
        click.echo(f"Total Cost: ${total_cost:.4f}")
        click.echo(f"Avg Cost per Problem: ${total_cost/len(problem_ids):.4f}")
        click.echo(f"Avg Iterations per Problem: {total_iterations/len(problem_ids):.1f}")

        # Baseline comparison
        baseline_comparison = None
        if baseline_model:
            baseline_total, baseline_found, baseline_missing = cost_registry.get_total_cost(
                baseline_model, problem_ids, dataset=dataset
            )
            if baseline_found > 0:
                click.echo(f"\n--- Baseline Comparison: {baseline_model} ---")
                click.echo(f"Baseline problems matched: {baseline_found}/{len(problem_ids)}")
                if baseline_missing > 0:
                    click.echo(f"  (Missing {baseline_missing} problems in registry)")
                click.echo(f"Baseline cost (median): ${baseline_total:.4f}")
                click.echo(f"Actual cost: ${total_cost:.4f}")
                savings = baseline_total - total_cost
                savings_pct = (savings / baseline_total * 100) if baseline_total > 0 else 0
                click.echo(f"Savings: ${savings:.4f} ({savings_pct:.1f}%)")
                baseline_comparison = {
                    "baseline_model": baseline_model,
                    "baseline_cost": baseline_total,
                    "baseline_problems_matched": baseline_found,
                    "baseline_problems_missing": baseline_missing,
                    "savings": savings,
                    "savings_pct": savings_pct,
                }

        # Store benchmark summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        success_rate = successes / len(problem_ids) * 100 if problem_ids else 0
        avg_cost = total_cost / len(problem_ids) if problem_ids else 0
        avg_iterations = total_iterations / len(problem_ids) if problem_ids else 0

        summary = {
            "run_id": benchmark_run_id,
            "mode": mode,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "config": {
                "local_model": local_model,
                "problem_range": f"{start}-{end}",
                "problems": problem_ids,
                "max_iterations": max_iterations,
                "no_spec": no_spec,
                "no_checkpoints": no_checkpoints,
                "no_cot": no_cot,
                "dataset": dataset,
                "temperature": temperature,
                "seed": seed
            },
            "results": [_build_result_entry(r) for r in results],
            "summary": {
                "total_problems": len(problem_ids),
                "successes": successes,
                "success_rate": success_rate,
                "total_cost": total_cost,
                "avg_cost": avg_cost,
                "avg_iterations": avg_iterations,
                **_aggregate_token_usage(results)
            },
            **({"baseline_comparison": baseline_comparison} if baseline_comparison else {})
        }

        # Store in Cortex
        try:
            asyncio.run(cortex.remember(
                title=f"Benchmark Run {benchmark_run_id}",
                content=json.dumps(summary, indent=2),
                category="architecture",
                tags=["benchmark_run", benchmark_run_id, mode, local_model],
                importance="critical",
                metadata=summary
            ))
            cortex_stored = True
        except Exception as e:
            click.echo(f"Warning: Failed to store in Cortex: {e}", err=True)
            cortex_stored = False

        # Save to file
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        results_file = results_dir / f"{benchmark_run_id}.json"
        results_file.write_text(json.dumps(summary, indent=2))

        click.echo(f"\n{'='*70}")
        click.echo("BENCHMARK SUMMARY SAVED")
        click.echo(f"{'='*70}")
        if cortex_stored:
            click.echo(f"Cortex: tags=['benchmark_run', '{benchmark_run_id}']")
        else:
            click.echo("Cortex: FAILED (see warning above)")
        click.echo(f"File: {results_file}")

        return 0


def _analyze_benchmark(bench_id, cortex, show_code):
    """Analyze a benchmark run by loading its JSON results and querying Cortex for each experiment."""

    click.echo(f"Analyzing benchmark run: {bench_id}\n")

    # Try to load benchmark results JSON
    results_file = Path("benchmark_results") / f"{bench_id}.json"
    bench_data = None

    if results_file.exists():
        bench_data = json.loads(results_file.read_text())
    else:
        click.echo(f"Benchmark results file not found: {results_file}")
        click.echo("Falling back to Cortex-only query...\n")

        # Query Cortex for the benchmark summary
        async def query_bench():
            memories = await cortex.export_memories(tags=[bench_id], category="architecture")
            return [m for m in memories if bench_id in m.get("tags", [])]

        bench_memories = asyncio.run(query_bench())
        if not bench_memories:
            click.echo(f"No data found for benchmark: {bench_id}")
            return 1

        # Try to parse benchmark data from memory content
        for mem in bench_memories:
            try:
                bench_data = json.loads(mem.get("content", "{}"))
                break
            except json.JSONDecodeError:
                continue

        if not bench_data:
            click.echo(f"Could not parse benchmark data from Cortex")
            return 1

    # Display benchmark summary
    click.echo("=" * 70)
    click.echo("BENCHMARK SUMMARY")
    click.echo("=" * 70)
    click.echo(f"Run ID: {bench_data.get('run_id', bench_id)}")
    click.echo(f"Mode: {bench_data.get('mode', 'unknown')}")

    config = bench_data.get("config", {})
    click.echo(f"Model: {config.get('local_model', 'unknown')}")
    click.echo(f"Problems: {config.get('problem_range', 'unknown')}")

    if bench_data.get("start_time"):
        click.echo(f"Started: {bench_data['start_time']}")
    if bench_data.get("duration_seconds"):
        duration = bench_data["duration_seconds"]
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        click.echo(f"Duration: {minutes}m {seconds}s")

    # Handle comparative vs single-mode benchmarks
    is_comparative = bench_data.get("mode") == "comparative"

    if is_comparative:
        for mode_key in ["zero_shot", "iterative"]:
            mode_data = bench_data.get(mode_key, {})
            summary = mode_data.get("summary", {})
            results_list = mode_data.get("results", [])

            mode_label = mode_key.replace("_", "-")
            click.echo(f"\n{'='*70}")
            click.echo(f"MODE: {mode_label.upper()}")
            click.echo(f"{'='*70}")
            click.echo(f"Success Rate: {summary.get('success_rate', 0):.1f}% ({summary.get('successes', 0)}/{summary.get('total_problems', 0)})")
            click.echo(f"Total Cost: ${summary.get('total_cost', 0):.4f}")
            click.echo(f"Avg Cost: ${summary.get('avg_cost', 0):.4f}")
            click.echo(f"Avg Iterations: {summary.get('avg_iterations', 0):.1f}")

            _display_experiment_table(results_list, cortex, show_code)
    else:
        summary = bench_data.get("summary", {})
        click.echo(f"\nSuccess Rate: {summary.get('success_rate', 0):.1f}% ({summary.get('successes', 0)}/{summary.get('total_problems', 0)})")
        click.echo(f"Total Cost: ${summary.get('total_cost', 0):.4f}")
        click.echo(f"Avg Cost: ${summary.get('avg_cost', 0):.4f}")
        click.echo(f"Avg Iterations: {summary.get('avg_iterations', 0):.1f}")

        results_list = bench_data.get("results", [])
        _display_experiment_table(results_list, cortex, show_code)

    return 0


def _display_experiment_table(results_list, cortex, show_code):
    """Display a table of experiment results with optional Cortex detail."""

    if not results_list:
        click.echo("\n  No experiment results found.")
        return

    click.echo(f"\n{'Problem':<20} | {'Exp ID':<16} | {'Status':<8} | {'Iters':<6} | {'Cost':<10}")
    click.echo(f"{'-'*20}-+-{'-'*16}-+-{'-'*8}-+-{'-'*6}-+-{'-'*10}")

    for r in results_list:
        status = "PASS" if r.get("success") else "FAIL"
        icon = "\u2713" if r.get("success") else "\u2717"
        click.echo(
            f"{r.get('problem_id', '?'):<20} | "
            f"{r.get('experiment_id', '?'):<16} | "
            f"{icon} {status:<5} | "
            f"{r.get('iterations', 0):<6} | "
            f"${r.get('cost', 0):<9.4f}"
        )

    # Show per-experiment Cortex details if show_code is enabled
    if show_code:
        for r in results_list:
            eid = r.get("experiment_id")
            if not eid:
                continue

            click.echo(f"\n{'='*60}")
            click.echo(f"DETAIL: {eid} ({r.get('problem_id', '?')})")
            click.echo(f"{'='*60}")

            async def query_exp(eid=eid):
                arch = await cortex.export_memories(tags=[eid], category="architecture")
                custom = await cortex.export_memories(tags=[eid], category="custom")
                learning = await cortex.export_memories(tags=[eid], category="learning")
                all_mems = arch + custom + learning
                return [m for m in all_mems if eid in m.get("tags", [])]

            exp_memories = asyncio.run(query_exp())

            for mem in exp_memories:
                tags = mem.get("tags", [])
                if "spec" in tags:
                    content = mem.get("content", "")
                    if "\n\nSpec:\n" in content:
                        spec_text = content.split("\n\nSpec:\n", 1)[1]
                        click.echo(f"  Spec: {spec_text[:200]}...")
                elif "result" in tags:
                    click.echo(f"  Result: {mem.get('content', '')[:200]}")


@cli.command()
@click.argument("exp_id")
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js"
)
@click.option(
    "--cortex-db",
    default=None,
    help="Path to cortex database file (defaults to CORTEX_DB env var or ~/.claude-cortex/koderz.db)"
)
@click.option(
    "--show-code",
    is_flag=True,
    help="Show code from iterations"
)
def analyze(exp_id, cortex_path, cortex_db, show_code):
    """Analyze a completed experiment by querying cortex."""

    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        return 1

    cortex_db = cortex_db or os.getenv("CORTEX_DB", DEFAULT_CORTEX_DB)
    cortex = CortexClient(cortex_path, db_path=cortex_db)

    # Handle benchmark run IDs (bench_ prefix)
    if exp_id.startswith("bench_"):
        return _analyze_benchmark(exp_id, cortex, show_code)

    click.echo(f"Analyzing experiment: {exp_id}\n")

    # Query all memories for this experiment across all relevant categories
    async def query():
        arch = await cortex.export_memories(tags=[exp_id], category="architecture")
        custom = await cortex.export_memories(tags=[exp_id], category="custom")
        learning = await cortex.export_memories(tags=[exp_id], category="learning")
        return arch + custom + learning

    memories = asyncio.run(query())

    # Exact tag filtering to prevent cross-experiment contamination
    memories = [m for m in memories if exp_id in m.get("tags", [])]

    if not memories:
        click.echo(f"No data found for experiment: {exp_id}")
        click.echo("\nTip: Use 'koderz results' to list all experiments")
        return 1

    # Organize memories by type
    spec = None
    iterations = []
    result = None

    for mem in memories:
        tags = mem.get("tags", [])
        if "spec" in tags:
            spec = mem
        elif "iteration" in tags:
            iterations.append(mem)
        elif "result" in tags:
            result = mem

    # Display spec
    if spec:
        click.echo("=" * 60)
        click.echo("SPECIFICATION")
        click.echo("=" * 60)
        content = spec.get("content", "")
        if "\n\nSpec:\n" in content:
            spec_text = content.split("\n\nSpec:\n", 1)[1]
            click.echo(spec_text[:500] + "..." if len(spec_text) > 500 else spec_text)
        click.echo()

    # Display iterations
    if iterations:
        click.echo("=" * 60)
        click.echo(f"ITERATIONS ({len(iterations)} total)")
        click.echo("=" * 60)

        # Sort by iteration number
        iterations.sort(key=lambda x: x.get("metadata", {}).get("iteration", 0))

        for iter_mem in iterations:
            metadata = iter_mem.get("metadata", {})
            iter_num = metadata.get("iteration", "?")
            success = metadata.get("success", False)
            error = metadata.get("error", "")
            tests_passed = metadata.get("tests_passed", 0)
            tests_total = metadata.get("tests_total", 0)
            test_pass_rate = metadata.get("test_pass_rate", 0.0)

            # Determine status icon and label
            if success:
                status_icon = "✓"
                status_label = "PASS"
            elif tests_passed > 0 and tests_passed < tests_total:
                status_icon = "⚠"
                status_label = "PARTIAL"
            else:
                status_icon = "✗"
                status_label = "FAIL"

            # Format test results
            if tests_total > 0:
                test_info = f" ({tests_passed}/{tests_total} tests, {test_pass_rate*100:.0f}%)"
            else:
                test_info = ""

            click.echo(f"\n{status_icon} Iteration {iter_num}: {status_label}{test_info}")

            if not success and error:
                # Truncate long errors
                error_preview = error[:150] + "..." if len(error) > 150 else error
                click.echo(f"   Error: {error_preview}")

            if show_code:
                content = iter_mem.get("content", "")
                if "Code:\n```python\n" in content:
                    code = content.split("Code:\n```python\n", 1)[1].split("\n```", 1)[0]
                    click.echo(f"   Code preview:\n{code[:200]}...")
                elif content:
                    # Content is just the code itself
                    click.echo(f"   Code preview:\n{content[:200]}...")

        click.echo()

    # Display final result
    if result:
        click.echo("=" * 60)
        click.echo("FINAL RESULT")
        click.echo("=" * 60)
        content = result.get("content", "")
        click.echo(content)

    return 0


@cli.command()
@click.argument("exp_id")
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js"
)
@click.option(
    "--cortex-db",
    default=None,
    help="Path to cortex database file (defaults to CORTEX_DB env var or ~/.claude-cortex/koderz.db)"
)
@click.option(
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
def show_spec(exp_id, cortex_path, cortex_db, humaneval_path):
    """Show the specification/prompt for an experiment.

    First tries to retrieve the spec from Cortex memory, then falls back
    to showing the original HumanEval problem if available.
    """
    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        return 1

    cortex_db = cortex_db or os.getenv("CORTEX_DB", DEFAULT_CORTEX_DB)
    cortex = CortexClient(cortex_path, db_path=cortex_db)

    click.echo(f"Looking up specification for: {exp_id}\n")

    # Try to find the spec in Cortex
    async def query_spec():
        # Look for spec memory with this exp_id
        # Specs are tagged with: ["experiment", "spec", exp_id, problem_id]
        # Check both architecture (new) and custom (old) categories
        arch_memories = await cortex.export_memories(category="architecture")
        custom_memories = await cortex.export_memories(category="custom")
        all_memories = arch_memories + custom_memories

        # Filter for memories that have both "spec" and exp_id in tags
        spec_mems = [
            m for m in all_memories
            if "spec" in m.get("tags", []) and exp_id in m.get("tags", [])
        ]
        return spec_mems

    spec_memories = asyncio.run(query_spec())

    problem_id = None
    spec_content = None

    if spec_memories:
        # Found the spec in memory
        spec_mem = spec_memories[0]
        content = spec_mem.get("content", "")
        tags = spec_mem.get("tags", [])

        # Extract problem_id from tags
        problem_tags = [t for t in tags if t.startswith("HumanEval/")]
        if problem_tags:
            problem_id = problem_tags[0]

        click.echo("=" * 80)
        click.echo("STORED SPECIFICATION (from Cortex)")
        click.echo("=" * 80)

        # Extract the problem and spec from content
        if "Problem:\n" in content and "\n\nSpec:\n" in content:
            parts = content.split("\n\nSpec:\n")
            problem_part = parts[0].replace("Problem:\n", "")
            spec_part = parts[1] if len(parts) > 1 else ""

            click.echo("\nOriginal Problem:")
            click.echo(problem_part)
            click.echo("\n" + "=" * 80)
            click.echo("Generated Specification:")
            click.echo("=" * 80)
            click.echo(spec_part)
        else:
            click.echo(content)

        return 0

    # Spec not in memory, try to get problem_id from result
    click.echo("⚠ Spec not found in Cortex (may have been consolidated)")
    click.echo("Attempting to show original HumanEval problem...\n")

    async def query_result():
        # Get all result memories and filter for this exp_id
        all_results = await cortex.export_memories(category="learning")
        results = [
            m for m in all_results
            if exp_id in m.get("tags", []) and "result" in m.get("tags", [])
        ]
        return results

    result_memories = asyncio.run(query_result())

    if result_memories:
        result_mem = result_memories[0]
        tags = result_mem.get("tags", [])
        problem_tags = [t for t in tags if t.startswith("HumanEval/")]
        if problem_tags:
            problem_id = problem_tags[0]

    if not problem_id:
        click.echo(f"Error: Could not determine problem ID for experiment {exp_id}")
        click.echo("This experiment may not exist or has been deleted.")
        return 1

    # Load HumanEval and show the original problem
    try:
        humaneval = HumanEval(data_path=humaneval_path)
        problem = benchmark_loader.get_problem(problem_id)

        click.echo("=" * 80)
        click.echo(f"ORIGINAL HUMANEVAL PROBLEM: {problem_id}")
        click.echo("=" * 80)
        click.echo(problem.get("prompt", ""))

        if problem.get("test"):
            click.echo("\n" + "=" * 80)
            click.echo("TEST CASES")
            click.echo("=" * 80)
            # Show first few lines of test
            test_lines = problem["test"].split("\n")[:10]
            click.echo("\n".join(test_lines))
            if len(problem["test"].split("\n")) > 10:
                click.echo("... (truncated)")

        click.echo("\n" + "=" * 80)
        click.echo("NOTE: Generated spec was not saved or was consolidated away.")
        click.echo("To preserve specs, increase their importance in orchestrator.py")
        click.echo("=" * 80)

    except Exception as e:
        click.echo(f"Error loading HumanEval problem: {e}")
        return 1

    return 0


@cli.command()
@click.option(
    "--humaneval-path",
    default=None,
    help="Path to dataset JSONL file"
)
@click.option(
    "--full",
    is_flag=True,
    help="Show full problem details instead of summary"
)
@click.option(
    "--limit",
    default=20,
    type=int,
    help="Number of problems to show (default: 20, use 0 for all)"
)
@click.option(
    "--problem-id",
    default=None,
    help="Show only a specific problem (e.g., HumanEval/0 or BigCodeBench/0)"
)
@click.option(
    "--dataset",
    type=click.Choice(["humaneval", "humaneval+", "bigcodebench", "bigcodebench-hard"], case_sensitive=False),
    default="humaneval",
    help="Dataset: humaneval, humaneval+, bigcodebench, or bigcodebench-hard"
)
def list_problems(humaneval_path, full, limit, problem_id, dataset):
    """List available benchmark problems.

    Examples:
      # List first 20 HumanEval problems (summary)
      koderz list-problems

      # Show full details for first 5 problems
      koderz list-problems --full --limit 5

      # Show specific problem in full
      koderz list-problems --problem-id HumanEval/0 --full

      # List BigCodeBench-Hard problems
      koderz list-problems --dataset bigcodebench-hard
    """

    # Load appropriate benchmark
    is_bigcodebench = dataset.lower().startswith("bigcodebench")
    if is_bigcodebench:
        benchmark = BigCodeBench(data_path=humaneval_path, dataset=dataset)
        download_cmd = f"koderz download-data --dataset {dataset}"
    else:
        benchmark = HumanEval(data_path=humaneval_path, dataset=dataset)
        download_cmd = "koderz download-data --dataset humaneval+"

    click.echo(f"{dataset} Dataset: {benchmark.count()} problems\n")

    if benchmark.count() == 0:
        click.echo(f"No problems found for dataset '{dataset}'.")
        click.echo(f"Download it with: {download_cmd}")
        return 1

    # Filter for specific problem if requested
    if problem_id:
        try:
            problem = benchmark.get_problem(problem_id)
            click.echo("=" * 80)
            click.echo(f"PROBLEM: {problem_id}")
            click.echo("=" * 80)
            click.echo(problem.get("prompt", problem.get("complete_prompt", "")))

            if full and problem.get("test"):
                click.echo("\n" + "=" * 80)
                click.echo("TEST CASES")
                click.echo("=" * 80)
                click.echo(problem["test"])

            if full and problem.get("entry_point"):
                click.echo("\n" + "=" * 80)
                click.echo(f"ENTRY POINT: {problem['entry_point']}")
                click.echo("=" * 80)

            # Show libs for BigCodeBench
            if full and is_bigcodebench and problem.get("libs"):
                click.echo("\n" + "=" * 80)
                click.echo(f"REQUIRED LIBRARIES: {', '.join(problem['libs'])}")
                click.echo("=" * 80)

            return 0
        except KeyError:
            click.echo(f"Error: Problem ID not found: {problem_id}")
            return 1

    # List all problems
    all_problems = benchmark.list_problems()

    # Apply limit (0 means no limit)
    if limit == 0:
        problems_to_show = all_problems
    else:
        problems_to_show = all_problems[:limit]

    for i, pid in enumerate(problems_to_show, 1):
        problem = benchmark.get_problem(pid)

        if full:
            # Show full problem details
            click.echo("=" * 80)
            click.echo(f"{i}. PROBLEM: {pid}")
            click.echo("=" * 80)
            click.echo(problem.get("prompt", ""))

            if problem.get("test"):
                click.echo("\n" + "-" * 80)
                click.echo("TEST CASES:")
                click.echo("-" * 80)
                # Show first 15 lines of tests
                test_lines = problem["test"].split("\n")[:15]
                click.echo("\n".join(test_lines))
                if len(problem["test"].split("\n")) > 15:
                    click.echo("... (truncated, use --problem-id to see full tests)")

            click.echo("\n")
        else:
            # Show summary (first line only)
            prompt_text = problem.get("prompt", problem.get("complete_prompt", ""))
            first_line = prompt_text.split("\n")[0][:60]
            click.echo(f"{i:3d}. {pid:20s} - {first_line}...")

    if len(all_problems) > len(problems_to_show):
        remaining = len(all_problems) - len(problems_to_show)
        click.echo(f"\n... and {remaining} more")
        click.echo(f"Use --limit 0 to see all problems")

    return 0


@cli.command()
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js"
)
@click.option(
    "--cortex-db",
    default=None,
    help="Path to cortex database file (defaults to CORTEX_DB env var or ~/.claude-cortex/koderz.db)"
)
@click.option(
    "--limit",
    default=20,
    type=int,
    help="Maximum number of results to show"
)
@click.option(
    "--problem",
    default=None,
    help="Filter by problem ID (e.g., HumanEval/0)"
)
@click.option(
    "--success-only",
    is_flag=True,
    help="Show only successful experiments"
)
def results(cortex_path, cortex_db, limit, problem, success_only):
    """Query and display experiment results from Cortex."""

    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        click.echo("Set via --cortex-path or CORTEX_PATH env var", err=True)
        return 1

    cortex_db = cortex_db or os.getenv("CORTEX_DB", DEFAULT_CORTEX_DB)
    cortex = CortexClient(cortex_path, db_path=cortex_db)

    async def query():
        # Build tag filter
        tags = ["result", "completed"]
        if problem:
            tags.append(problem)

        # Export all matching memories
        memories = await cortex.export_memories(
            tags=tags,
            category="learning"
        )
        return memories

    click.echo("Querying Cortex for experiment results...\n")
    memories = asyncio.run(query())

    if not memories:
        click.echo("No experiment results found.")
        click.echo("\nTip: Run an experiment first with:")
        click.echo("  python -m koderz.cli run --problem-id HumanEval/0")
        return 0

    # Parse and display results
    displayed = 0
    for mem in memories:
        metadata = mem.get("metadata", {})
        content = mem.get("content", "")
        tags = mem.get("tags", [])

        # Extract exp_id from tags if not in metadata
        exp_id = metadata.get("experiment_id")
        if not exp_id or exp_id == "unknown":
            # Look for exp_* in tags
            exp_tags = [t for t in tags if t.startswith("exp_")]
            exp_id = exp_tags[0] if exp_tags else "unknown"

        # Skip non-experiment memories
        if exp_id == "unknown":
            continue

        # Extract problem_id from tags if not in metadata
        problem_id = metadata.get("problem_id")
        if not problem_id or problem_id == "unknown":
            # Look for HumanEval/* in tags
            problem_tags = [t for t in tags if t.startswith("HumanEval/")]
            problem_id = problem_tags[0] if problem_tags else "unknown"

        # Parse success and iterations from content if not in metadata
        success = metadata.get("success", False)
        iterations = metadata.get("iterations", 0)
        if not success and "Success: " in content:
            success_line = [line for line in content.split("\n") if line.startswith("Success: ")]
            if success_line:
                success = success_line[0].split("Success: ")[1].strip() == "True"
        if iterations == 0 and "Total Iterations: " in content:
            iter_line = [line for line in content.split("\n") if line.startswith("Total Iterations: ")]
            if iter_line:
                try:
                    iterations = int(iter_line[0].split("Total Iterations: ")[1].strip())
                except:
                    pass

        # Filter by success if requested
        if success_only and not success:
            continue

        # Parse cost info from content if not in metadata
        actual_cost = metadata.get("actual_cost", 0.0)
        baseline_cost = metadata.get("baseline_cost", 0.0)
        savings = metadata.get("savings", 0.0)
        savings_pct = metadata.get("savings_pct", 0.0)

        if actual_cost == 0.0 and "Actual Total: $" in content:
            try:
                cost_line = [line for line in content.split("\n") if "Actual Total: $" in line]
                if cost_line:
                    actual_cost = float(cost_line[0].split("$")[1].split()[0])
            except:
                pass

        if baseline_cost == 0.0 and "Frontier-Only Estimate: $" in content:
            try:
                baseline_line = [line for line in content.split("\n") if "Frontier-Only Estimate: $" in line]
                if baseline_line:
                    baseline_cost = float(baseline_line[0].split("$")[1].split()[0])
            except:
                pass

        if savings == 0.0 and "Savings: $" in content:
            try:
                savings_line = [line for line in content.split("\n") if "Savings: $" in line]
                if savings_line:
                    parts = savings_line[0].split("$")[1].split()
                    savings = float(parts[0])
                    if "(" in savings_line[0]:
                        savings_pct = float(savings_line[0].split("(")[1].split("%")[0])
            except:
                pass

        # Display formatted result
        status_icon = "✓" if success else "✗"
        status_color = "green" if success else "red"

        click.echo(f"{status_icon} {exp_id}")
        click.echo(f"   Problem: {problem_id}")
        click.echo(f"   Status: {'SUCCESS' if success else 'FAILED'} after {iterations} iterations")
        click.echo(f"   Cost: ${actual_cost:.4f} (vs ${baseline_cost:.4f} baseline)")

        if savings > 0:
            click.echo(f"   Savings: ${savings:.4f} ({savings_pct:.1f}%)")

        click.echo()

        displayed += 1
        if displayed >= limit:
            break

    if displayed == 0:
        click.echo("No results match your filters.")
    else:
        click.echo(f"Showing {displayed} of {len(memories)} total results")
        if displayed < len(memories):
            click.echo(f"Use --limit {len(memories)} to see all results")

    return 0


@cli.command("frontier-costs")
@click.option(
    "--model",
    default=None,
    help="Show costs for a specific model"
)
@click.option(
    "--problem",
    default=None,
    help="Show costs for a specific problem (e.g., HumanEval/0)"
)
@click.option(
    "--dataset",
    type=click.Choice(["humaneval", "humaneval+"], case_sensitive=False),
    default=None,
    help="Filter by dataset"
)
@click.option(
    "--prune-days",
    default=None,
    type=int,
    help="Prune runs older than N days (use with --confirm)"
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm destructive operations"
)
def frontier_costs(model, problem, dataset, prune_days, confirm):
    """View and manage the frontier cost registry.

    \b
    Examples:
      # List all models with recorded costs
      koderz frontier-costs

      # Show costs for a specific model
      koderz frontier-costs --model gpt-5-mini

      # Show costs for a specific problem
      koderz frontier-costs --model gpt-5-mini --problem HumanEval/0

      # Filter by dataset
      koderz frontier-costs --model gpt-5-mini --dataset humaneval+

      # Prune old runs (dry run)
      koderz frontier-costs --prune-days 30

      # Prune old runs (actually delete)
      koderz frontier-costs --prune-days 30 --confirm
    """
    registry = FrontierCostRegistry()

    # Handle prune operation
    if prune_days is not None:
        dry_run = not confirm
        removed = registry.prune_old_runs(prune_days, dry_run=dry_run)
        total_removed = sum(removed.values())

        if dry_run:
            click.echo(f"DRY RUN: Would remove {total_removed} runs older than {prune_days} days")
            for model_name, count in removed.items():
                if count > 0:
                    click.echo(f"  {model_name}: {count} runs")
            click.echo("\nRun with --confirm to actually delete")
        else:
            click.echo(f"Removed {total_removed} runs older than {prune_days} days")
            for model_name, count in removed.items():
                if count > 0:
                    click.echo(f"  {model_name}: {count} runs")
        return 0

    # Show specific problem details
    if model and problem:
        details = registry.get_run_details(model, problem)
        if not details:
            click.echo(f"No costs recorded for {model} on {problem}")
            return 1

        click.echo(f"=== {model} - {problem} ===")
        click.echo(f"Median cost: ${details['median_cost']:.6f}")
        click.echo(f"Total runs: {details['run_count']}")
        click.echo()

        for i, run in enumerate(details['runs'], 1):
            config = run.get('config', {})
            tokens = run.get('tokens', {})
            click.echo(f"Run {i}: ${run['cost']:.6f}")
            click.echo(f"  Timestamp: {run['timestamp']}")
            click.echo(f"  Success: {run.get('success', 'N/A')}")
            click.echo(f"  Tokens: {tokens.get('input', 0)} in / {tokens.get('output', 0)} out")
            click.echo(f"  Config: dataset={config.get('dataset')}, temp={config.get('temperature')}")
            click.echo()
        return 0

    # Show model summary
    if model:
        summary = registry.get_model_summary(model, dataset=dataset)
        if summary['problem_count'] == 0:
            click.echo(f"No costs recorded for {model}" + (f" (dataset={dataset})" if dataset else ""))
            return 1

        click.echo(f"=== {model} ===" + (f" (dataset={dataset})" if dataset else ""))
        click.echo(f"Problems: {summary['problem_count']}")
        click.echo(f"Total median cost: ${summary['total_median_cost']:.4f}")
        click.echo(f"Avg cost/problem: ${summary['avg_cost_per_problem']:.6f}")
        click.echo()

        # List problems
        problems = registry.list_problems(model)
        click.echo(f"{'Problem':<20} {'Median Cost':<12} {'Runs':<6}")
        click.echo("-" * 40)
        for pid in sorted(problems):
            cost = registry.get_cost(model, pid, dataset=dataset)
            if cost is not None:
                details = registry.get_run_details(model, pid)
                click.echo(f"{pid:<20} ${cost:<11.6f} {details['run_count']:<6}")
        return 0

    # List all models
    models = registry.list_models()
    if not models:
        click.echo("No frontier costs recorded yet.")
        click.echo("Run a benchmark with a frontier model (gpt-5-mini, claude-haiku-4-5, etc.) to record costs.")
        return 0

    click.echo("=== Frontier Cost Registry ===")
    click.echo()
    click.echo(f"{'Model':<25} {'Problems':<10} {'Total Cost':<12} {'Avg/Problem':<12}")
    click.echo("-" * 60)

    for model_name in sorted(models):
        summary = registry.get_model_summary(model_name, dataset=dataset)
        if summary['problem_count'] > 0:
            click.echo(
                f"{model_name:<25} {summary['problem_count']:<10} "
                f"${summary['total_median_cost']:<11.4f} ${summary['avg_cost_per_problem']:<11.6f}"
            )

    click.echo()
    click.echo("Use --model <name> for details, --model <name> --problem <id> for run history")
    return 0


@cli.command("download-data")
@click.option(
    "--dataset",
    type=click.Choice(["humaneval", "humaneval+", "bigcodebench", "bigcodebench-hard"], case_sensitive=False),
    default="humaneval+",
    help="Dataset to download (default: humaneval+)"
)
def download_data(dataset):
    """Download benchmark datasets.

    Downloads dataset files to the koderz/data/ directory.

    Examples:

        \b
        # Download HumanEval+ (default)
        koderz download-data

        \b
        # Download BigCodeBench-Hard (148 tasks)
        koderz download-data --dataset bigcodebench-hard

        \b
        # Download full BigCodeBench (1140 tasks)
        koderz download-data --dataset bigcodebench
    """
    import urllib.request

    dataset_lower = dataset.lower()

    if dataset_lower == "humaneval":
        click.echo("HumanEval dataset ships with the package.")
        click.echo("If missing, download from: https://github.com/openai/human-eval")
        return 0

    if dataset_lower == "humaneval+":
        filename = HUMANEVAL_DATASET_FILES["humaneval+"]
        gz_filename = filename + ".gz"
        url = f"https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/{gz_filename}"

        package_dir = Path(__file__).parent
        data_dir = package_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        dest = data_dir / gz_filename

        # Also check for uncompressed variant
        dest_plain = data_dir / filename

        if dest.exists() or dest_plain.exists():
            existing = dest if dest.exists() else dest_plain
            click.echo(f"File already exists: {existing}")
            # Verify by loading
            benchmark = HumanEval(dataset="humaneval+")
            click.echo(f"Loaded {benchmark.count()} problems.")
            return 0

        click.echo(f"Downloading {gz_filename}...")
        click.echo(f"  URL: {url}")
        click.echo(f"  Destination: {dest}")

        try:
            urllib.request.urlretrieve(url, str(dest))
            click.echo("Download complete.")
        except Exception as e:
            click.echo(f"Error downloading: {e}", err=True)
            click.echo("\nManual download:", err=True)
            click.echo(f"  curl -L -o {dest} {url}", err=True)
            return 1

        # Verify
        benchmark = HumanEval(dataset="humaneval+")
        click.echo(f"Loaded {benchmark.count()} problems from {gz_filename}")
        return 0

    if dataset_lower.startswith("bigcodebench"):
        # BigCodeBench requires the 'datasets' library from HuggingFace
        try:
            from datasets import load_dataset
        except ImportError:
            click.echo("Error: 'datasets' package not installed.", err=True)
            click.echo("Install with: pip install datasets", err=True)
            click.echo("Or: poetry add datasets", err=True)
            return 1

        package_dir = Path(__file__).parent
        data_dir = package_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Determine output file and subset
        if dataset_lower == "bigcodebench-hard":
            output_file = data_dir / BCB_DATASET_FILES["bigcodebench-hard"]
            subset = "hard"
            max_tasks = 148
        else:
            output_file = data_dir / BCB_DATASET_FILES["bigcodebench"]
            subset = "full"
            max_tasks = None

        if output_file.exists():
            click.echo(f"File already exists: {output_file}")
            benchmark = BigCodeBench(dataset=dataset_lower)
            click.echo(f"Loaded {benchmark.count()} problems.")
            return 0

        click.echo(f"Downloading BigCodeBench ({subset} subset) from HuggingFace...")

        try:
            ds = load_dataset("bigcode/bigcodebench", split="v0.1.2", trust_remote_code=True)
        except Exception as e:
            click.echo(f"Error loading dataset: {e}", err=True)
            click.echo("\nTry installing the datasets package:", err=True)
            click.echo("  pip install datasets", err=True)
            return 1

        click.echo(f"Loaded {len(ds)} total tasks from HuggingFace")

        # Convert to JSONL format
        count = 0
        with open(output_file, 'w') as f:
            for item in ds:
                if max_tasks is not None and count >= max_tasks:
                    break

                # Handle libs field - it might be a string that needs parsing
                libs = item.get("libs", [])
                if isinstance(libs, str):
                    try:
                        libs = json.loads(libs)
                    except json.JSONDecodeError:
                        libs = [libs] if libs else []

                problem = {
                    "task_id": item.get("task_id", f"BigCodeBench/{count}"),
                    "complete_prompt": item.get("complete_prompt", item.get("prompt", "")),
                    "instruct_prompt": item.get("instruct_prompt", ""),
                    "entry_point": item.get("entry_point", ""),
                    "test": item.get("test", ""),
                    "canonical_solution": item.get("canonical_solution", item.get("solution", "")),
                    "libs": libs,
                    # Also store prompt for compatibility with HumanEval interface
                    "prompt": item.get("complete_prompt", item.get("prompt", "")),
                }

                f.write(json.dumps(problem) + "\n")
                count += 1

        click.echo(f"Successfully wrote {count} tasks to {output_file}")

        # Verify
        benchmark = BigCodeBench(dataset=dataset_lower)
        click.echo(f"Verified: Loaded {benchmark.count()} problems")
        return 0

    click.echo(f"Unknown dataset: {dataset}", err=True)
    return 1


@cli.command("speed-test")
@click.argument("models", nargs=-1, required=True)
@click.option(
    "--export",
    default=None,
    help="Export results to JSON file (e.g., speed_results.json)"
)
@click.option(
    "--host",
    default=None,
    help="Ollama host URL (defaults to OLLAMA_HOST env var or http://localhost:11434)"
)
@click.option(
    "--warmup/--no-warmup",
    default=True,
    help="Run warmup prompt to load model into memory before testing (default: enabled)"
)
@click.option(
    "--timeout",
    default=300,
    type=int,
    help="Request timeout in seconds for Ollama (default: 300)"
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum retry attempts for Ollama timeouts/overload (default: 3)"
)
def speed_test(models, export, host, warmup, timeout, max_retries):
    """Benchmark model inference speed.

    Tests each model with standard prompts (essay, coding, brain teaser)
    and reports tokens/sec and total time.

    By default, runs a warmup prompt first to load the model into memory,
    ensuring accurate speed measurements without model loading overhead.

    Examples:

        \b
        # Test single model (with warmup, default)
        koderz speed-test qwen2.5-coder:32b

        \b
        # Test multiple models
        koderz speed-test qwen2.5-coder:32b deepseek-coder:33b codellama:70b

        \b
        # Test without warmup
        koderz speed-test qwen2.5-coder:32b --no-warmup

        \b
        # Export results
        koderz speed-test qwen2.5-coder:32b --export speed_results.json
    """
    from .benchmarks.speed_test import ModelSpeedBenchmark

    # Use OLLAMA_HOST env var if --host not provided
    if host is None:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    click.echo("=" * 80)
    click.echo("MODEL SPEED BENCHMARK")
    click.echo("=" * 80)
    click.echo(f"\nTesting {len(models)} model(s): {', '.join(models)}")
    click.echo(f"Host: {host}")
    click.echo(f"Warmup: {'enabled' if warmup else 'disabled'}")
    click.echo(f"Timeout: {timeout}s")
    click.echo(f"Max retries: {max_retries}")
    if warmup:
        click.echo("  (Running quick warmup task to load each model into memory)")
    click.echo()

    benchmark = ModelSpeedBenchmark(host=host, timeout=timeout, max_retries=max_retries)

    try:
        results = benchmark.benchmark_models(list(models), warmup=warmup)

        if not results:
            click.echo("\n✗ No successful tests. Check model names and ollama status.")
            return 1

        # Print results
        benchmark.print_results(results)

        # Export if requested
        if export:
            benchmark.export_json(results, export)

        return 0

    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    cli()
