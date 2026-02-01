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
from .benchmarks.humaneval import HumanEval


# Load environment variables
load_dotenv()

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
    num_ctx
):
    """Run a single experiment on a HumanEval problem."""

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

    # Initialize clients
    click.echo("Initializing clients...")
    model_factory = ModelFactory(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
        num_ctx=num_ctx
    )

    # Load HumanEval
    click.echo("Loading HumanEval dataset...")
    humaneval = HumanEval(data_path=humaneval_path)

    try:
        problem = humaneval.get_problem(problem_id)
    except KeyError:
        click.echo(f"Error: Problem ID not found: {problem_id}", err=True)
        click.echo(f"Available problems: {humaneval.count()}", err=True)
        return 1

    # Run experiment (using one-shot Cortex sessions for now to avoid blocking issues)
    cortex = CortexClient(cortex_path, db_path=cortex_db)
    orchestrator = ExperimentOrchestrator(
        cortex=cortex,
        model_factory=model_factory,
        checkpoint_interval=checkpoint_interval,
        debug=debug,
        debug_dir=debug_dir
    )

    result = asyncio.run(
        orchestrator.run_experiment(
            problem=problem,
            max_iterations=max_iterations,
            local_model=local_model,
            frontier_spec_model=frontier_spec_model,
            frontier_checkpoint_model=frontier_checkpoint_model,
            reuse_spec=reuse_spec,
            mode=mode
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
def benchmark(start, end, local_model, max_iterations, cortex_path, cortex_db, humaneval_path, mode, debug, debug_dir, timeout, max_retries, num_ctx):
    """Run benchmark on a range of HumanEval problems.

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

    # Initialize clients
    cortex = CortexClient(cortex_path, db_path=cortex_db)
    model_factory = ModelFactory(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
        num_ctx=num_ctx
    )

    # Load HumanEval
    humaneval = HumanEval(data_path=humaneval_path)
    problem_ids = humaneval.list_problems()[start:end]

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

            problem = humaneval.get_problem(problem_id)

            # Run zero-shot
            click.echo("\n[ZERO-SHOT MODE]")
            orchestrator_zs = ExperimentOrchestrator(
                cortex=cortex,
                model_factory=model_factory,
                debug=debug,
                debug_dir=debug_dir
            )
            result_zs = asyncio.run(
                orchestrator_zs.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode="zero-shot",
                    benchmark_run_id=benchmark_run_id
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
                debug_dir=debug_dir
            )
            result_iter = asyncio.run(
                orchestrator_iter.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode="iterative",
                    benchmark_run_id=benchmark_run_id
                )
            )
            iterative_results.append(result_iter)
            iter_status = "✓ PASS" if result_iter["success"] else "✗ FAIL"
            click.echo(f"  {iter_status} | Cost: ${result_iter['cost_analysis']['actual_cost']:.4f} | Iterations: {result_iter['iterations']}")

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
                "max_iterations": max_iterations
            },
            "zero_shot": {
                "results": [
                    {
                        "experiment_id": r["experiment_id"],
                        "problem_id": r["problem_id"],
                        "success": r["success"],
                        "iterations": r["iterations"],
                        "cost": r["cost_analysis"]["actual_cost"]
                    }
                    for r in zero_shot_results
                ],
                "summary": {
                    "total_problems": len(zero_shot_results),
                    "successes": zs_successes,
                    "success_rate": zs_success_rate,
                    "total_cost": zs_total_cost,
                    "avg_cost": zs_avg_cost,
                    "avg_iterations": zs_avg_iters
                }
            },
            "iterative": {
                "results": [
                    {
                        "experiment_id": r["experiment_id"],
                        "problem_id": r["problem_id"],
                        "success": r["success"],
                        "iterations": r["iterations"],
                        "cost": r["cost_analysis"]["actual_cost"]
                    }
                    for r in iterative_results
                ],
                "summary": {
                    "total_problems": len(iterative_results),
                    "successes": iter_successes,
                    "success_rate": iter_success_rate,
                    "total_cost": iter_total_cost,
                    "avg_cost": iter_avg_cost,
                    "avg_iterations": iter_avg_iters
                }
            },
            "comparison": {
                "success_rate_improvement": success_improvement,
                "cost_difference": cost_diff,
                "iteration_difference": iter_diff
            }
        }

        # Store in Cortex
        asyncio.run(cortex.remember(
            title=f"Benchmark Run {benchmark_run_id}",
            content=json.dumps(summary, indent=2),
            category="architecture",
            tags=["benchmark_run", benchmark_run_id, "comparative", local_model],
            importance="critical",
            metadata=summary
        ))

        # Save to file
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        results_file = results_dir / f"{benchmark_run_id}.json"
        results_file.write_text(json.dumps(summary, indent=2))

        click.echo(f"\n{'='*70}")
        click.echo("BENCHMARK SUMMARY SAVED")
        click.echo(f"{'='*70}")
        click.echo(f"Cortex: tags=['benchmark_run', '{benchmark_run_id}']")
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

            problem = humaneval.get_problem(problem_id)

            orchestrator = ExperimentOrchestrator(
                cortex=cortex,
                model_factory=model_factory,
                debug=debug,
                debug_dir=debug_dir
            )

            result = asyncio.run(
                orchestrator.run_experiment(
                    problem=problem,
                    max_iterations=max_iterations,
                    local_model=local_model,
                    mode=mode,
                    benchmark_run_id=benchmark_run_id
                )
            )

            results.append(result)
            if result["success"]:
                successes += 1

            total_cost += result["cost_analysis"]["actual_cost"]
            total_iterations += result["iterations"]

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
                "max_iterations": max_iterations
            },
            "results": [
                {
                    "experiment_id": r["experiment_id"],
                    "problem_id": r["problem_id"],
                    "success": r["success"],
                    "iterations": r["iterations"],
                    "cost": r["cost_analysis"]["actual_cost"]
                }
                for r in results
            ],
            "summary": {
                "total_problems": len(problem_ids),
                "successes": successes,
                "success_rate": success_rate,
                "total_cost": total_cost,
                "avg_cost": avg_cost,
                "avg_iterations": avg_iterations
            }
        }

        # Store in Cortex
        asyncio.run(cortex.remember(
            title=f"Benchmark Run {benchmark_run_id}",
            content=json.dumps(summary, indent=2),
            category="architecture",
            tags=["benchmark_run", benchmark_run_id, mode, local_model],
            importance="critical",
            metadata=summary
        ))

        # Save to file
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        results_file = results_dir / f"{benchmark_run_id}.json"
        results_file.write_text(json.dumps(summary, indent=2))

        click.echo(f"\n{'='*70}")
        click.echo("BENCHMARK SUMMARY SAVED")
        click.echo(f"{'='*70}")
        click.echo(f"Cortex: tags=['benchmark_run', '{benchmark_run_id}']")
        click.echo(f"File: {results_file}")

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

    click.echo(f"Analyzing experiment: {exp_id}\n")

    # Query all memories for this experiment
    async def query():
        memories = await cortex.export_memories(
            tags=[exp_id],
            category="custom"
        )
        return memories

    memories = asyncio.run(query())

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
        problem = humaneval.get_problem(problem_id)

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
    help="Path to HumanEval.jsonl file"
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
    help="Show only a specific problem (e.g., HumanEval/0)"
)
def list_problems(humaneval_path, full, limit, problem_id):
    """List available HumanEval problems.

    Examples:
      # List first 20 problems (summary)
      koderz list-problems

      # Show full details for first 5 problems
      koderz list-problems --full --limit 5

      # Show specific problem in full
      koderz list-problems --problem-id HumanEval/0 --full
    """

    humaneval = HumanEval(data_path=humaneval_path)

    click.echo(f"HumanEval Dataset: {humaneval.count()} problems\n")

    if humaneval.count() == 0:
        click.echo("No problems found. Download HumanEval.jsonl from:")
        click.echo("https://github.com/openai/human-eval")
        click.echo("\nPlace it in koderz/data/HumanEval.jsonl")
        return 1

    # Filter for specific problem if requested
    if problem_id:
        try:
            problem = humaneval.get_problem(problem_id)
            click.echo("=" * 80)
            click.echo(f"PROBLEM: {problem_id}")
            click.echo("=" * 80)
            click.echo(problem.get("prompt", ""))

            if full and problem.get("test"):
                click.echo("\n" + "=" * 80)
                click.echo("TEST CASES")
                click.echo("=" * 80)
                click.echo(problem["test"])

            if full and problem.get("entry_point"):
                click.echo("\n" + "=" * 80)
                click.echo(f"ENTRY POINT: {problem['entry_point']}")
                click.echo("=" * 80)

            return 0
        except KeyError:
            click.echo(f"Error: Problem ID not found: {problem_id}")
            return 1

    # List all problems
    all_problems = humaneval.list_problems()

    # Apply limit (0 means no limit)
    if limit == 0:
        problems_to_show = all_problems
    else:
        problems_to_show = all_problems[:limit]

    for i, pid in enumerate(problems_to_show, 1):
        problem = humaneval.get_problem(pid)

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
            first_line = problem["prompt"].split("\n")[0][:60]
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
