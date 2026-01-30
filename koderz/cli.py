"""CLI interface for koderz."""

import os
import asyncio
import click
from pathlib import Path
from dotenv import load_dotenv

from .orchestrator import ExperimentOrchestrator
from .cortex.client import CortexClient
from .models.local import OllamaClient
from .models.frontier import FrontierClient
from .benchmarks.humaneval import HumanEval


# Load environment variables
load_dotenv()


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
    default="claude-opus-4-5",
    help="Frontier model for spec generation"
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
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
def run(
    problem_id,
    local_model,
    frontier_spec_model,
    frontier_checkpoint_model,
    max_iterations,
    checkpoint_interval,
    cortex_path,
    humaneval_path
):
    """Run a single experiment on a HumanEval problem."""

    # Validate environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set in environment", err=True)
        click.echo("Create a .env file with: ANTHROPIC_API_KEY=sk-ant-...", err=True)
        return 1

    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path:
        click.echo("Error: CORTEX_PATH not set", err=True)
        click.echo("Set via --cortex-path or CORTEX_PATH env var", err=True)
        return 1

    if not Path(cortex_path).exists():
        click.echo(f"Error: Cortex path not found: {cortex_path}", err=True)
        return 1

    # Initialize clients
    click.echo("Initializing clients...")
    cortex = CortexClient(cortex_path)
    local = OllamaClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    frontier = FrontierClient(api_key)

    # Load HumanEval
    click.echo("Loading HumanEval dataset...")
    humaneval = HumanEval(data_path=humaneval_path)

    try:
        problem = humaneval.get_problem(problem_id)
    except KeyError:
        click.echo(f"Error: Problem ID not found: {problem_id}", err=True)
        click.echo(f"Available problems: {humaneval.count()}", err=True)
        return 1

    # Run experiment
    orchestrator = ExperimentOrchestrator(
        cortex=cortex,
        local=local,
        frontier=frontier,
        checkpoint_interval=checkpoint_interval
    )

    # Run async experiment
    result = asyncio.run(
        orchestrator.run_experiment(
            problem=problem,
            max_iterations=max_iterations,
            local_model=local_model,
            frontier_spec_model=frontier_spec_model,
            frontier_checkpoint_model=frontier_checkpoint_model
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
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
def benchmark(start, end, local_model, max_iterations, cortex_path, humaneval_path):
    """Run benchmark on a range of HumanEval problems."""

    # Validate environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
        return 1

    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        return 1

    # Initialize clients
    cortex = CortexClient(cortex_path)
    local = OllamaClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    frontier = FrontierClient(api_key)

    # Load HumanEval
    humaneval = HumanEval(data_path=humaneval_path)
    problem_ids = humaneval.list_problems()[start:end]

    click.echo(f"\nRunning benchmark on {len(problem_ids)} problems...")
    click.echo(f"Range: {start} to {end}")
    click.echo(f"Local model: {local_model}\n")

    # Track aggregate stats
    results = []
    successes = 0
    total_cost = 0.0

    for i, problem_id in enumerate(problem_ids, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"Problem {i}/{len(problem_ids)}: {problem_id}")
        click.echo(f"{'='*60}")

        problem = humaneval.get_problem(problem_id)

        orchestrator = ExperimentOrchestrator(
            cortex=cortex,
            local=local,
            frontier=frontier
        )

        result = asyncio.run(
            orchestrator.run_experiment(
                problem=problem,
                max_iterations=max_iterations,
                local_model=local_model
            )
        )

        results.append(result)
        if result["success"]:
            successes += 1

        total_cost += result["cost_analysis"]["actual_cost"]

    # Print aggregate results
    click.echo(f"\n{'='*60}")
    click.echo("BENCHMARK COMPLETE")
    click.echo(f"{'='*60}")
    click.echo(f"Problems: {len(problem_ids)}")
    click.echo(f"Successes: {successes} ({successes/len(problem_ids)*100:.1f}%)")
    click.echo(f"Total Cost: ${total_cost:.2f}")
    click.echo(f"Avg Cost per Problem: ${total_cost/len(problem_ids):.2f}")

    return 0


@cli.command()
@click.argument("exp_id")
@click.option(
    "--cortex-path",
    default=None,
    help="Path to cortex-core dist/index.js"
)
def analyze(exp_id, cortex_path):
    """Analyze a completed experiment by querying cortex."""

    cortex_path = cortex_path or os.getenv("CORTEX_PATH")
    if not cortex_path or not Path(cortex_path).exists():
        click.echo(f"Error: Invalid cortex path: {cortex_path}", err=True)
        return 1

    cortex = CortexClient(cortex_path)

    click.echo(f"Querying cortex for experiment: {exp_id}...")

    # Query all memories for this experiment
    async def query():
        memories = await cortex.recall(
            query=exp_id,
            limit=100,
            mode="recent"
        )
        return memories

    memories = asyncio.run(query())

    # Display results
    click.echo(f"\nFound {len(memories) if isinstance(memories, list) else 'some'} memories")
    click.echo("\nTo view full details, use Claude Code with cortex-core loaded:")
    click.echo(f"  /recall query:{exp_id}")

    return 0


@cli.command()
@click.option(
    "--humaneval-path",
    default=None,
    help="Path to HumanEval.jsonl file"
)
def list_problems(humaneval_path):
    """List available HumanEval problems."""

    humaneval = HumanEval(data_path=humaneval_path)

    click.echo(f"HumanEval Dataset: {humaneval.count()} problems\n")

    if humaneval.count() == 0:
        click.echo("No problems found. Download HumanEval.jsonl from:")
        click.echo("https://github.com/openai/human-eval")
        click.echo("\nPlace it in koderz/data/HumanEval.jsonl")
        return 1

    for i, problem_id in enumerate(humaneval.list_problems()[:20], 1):
        problem = humaneval.get_problem(problem_id)
        # Show first line of prompt
        first_line = problem["prompt"].split("\n")[0][:60]
        click.echo(f"{i:3d}. {problem_id:20s} - {first_line}...")

    if humaneval.count() > 20:
        click.echo(f"\n... and {humaneval.count() - 20} more")

    return 0


if __name__ == "__main__":
    cli()
