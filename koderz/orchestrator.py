"""Experiment orchestration logic."""

import uuid
import asyncio
from typing import Optional, Any
from datetime import datetime

from .cortex.client import CortexClient
from .models.local import OllamaClient
from .models.frontier import FrontierClient
from .benchmarks.humaneval import execute_solution
from .analysis.cost import CostAnalyzer


class ExperimentOrchestrator:
    """Orchestrates coding experiments with swarm of local + frontier models."""

    def __init__(
        self,
        cortex: CortexClient,
        local: OllamaClient,
        frontier: FrontierClient,
        checkpoint_interval: int = 5
    ):
        """Initialize orchestrator.

        Args:
            cortex: Cortex MCP client
            local: Local model client
            frontier: Frontier model client
            checkpoint_interval: Checkpoint every N iterations
        """
        self.cortex = cortex
        self.local = local
        self.frontier = frontier
        self.checkpoint_interval = checkpoint_interval
        self.cost_analyzer = CostAnalyzer()

    async def run_experiment(
        self,
        problem: dict,
        max_iterations: int = 50,
        local_model: str = "codellama:70b",
        frontier_spec_model: str = "claude-opus-4-5",
        frontier_checkpoint_model: str = "claude-sonnet-4-5"
    ) -> dict:
        """Run a complete experiment on a problem.

        Args:
            problem: HumanEval problem dictionary
            max_iterations: Maximum iterations before giving up
            local_model: Local model to use for iterations
            frontier_spec_model: Frontier model for spec generation
            frontier_checkpoint_model: Frontier model for checkpoints

        Returns:
            Experiment result dictionary
        """
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        problem_id = problem.get("task_id", "unknown")

        print(f"\n{'='*60}")
        print(f"Starting Experiment: {exp_id}")
        print(f"Problem: {problem_id}")
        print(f"{'='*60}\n")

        # Start session
        await self.cortex.start_session(context=f"Experiment {exp_id} - {problem_id}")

        # Phase 1: Generate spec with frontier model
        print(f"Phase 1: Generating spec with {frontier_spec_model}...")
        spec_result = self.frontier.generate_spec(
            problem["prompt"],
            model=frontier_spec_model
        )

        self.cost_analyzer.add_frontier_cost(
            spec_result["cost"],
            frontier_spec_model,
            "spec"
        )

        # Store spec in cortex
        await self.cortex.remember(
            title=f"Experiment: {problem_id}",
            content=f"Problem:\n{problem['prompt']}\n\nSpec:\n{spec_result['spec']}",
            category="custom",
            tags=["experiment", "spec", exp_id, problem_id],
            importance="high",
            metadata={
                "experiment_id": exp_id,
                "problem_id": problem_id,
                "model": frontier_spec_model,
                "cost": spec_result["cost"],
                "timestamp": datetime.now().isoformat()
            }
        )

        print(f"  Spec generated (cost: ${spec_result['cost']:.4f})")
        print(f"  Stored in cortex\n")

        # Phase 2: Iterative execution with local model
        print(f"Phase 2: Iterative execution with {local_model}...")

        checkpoint_guidance = None

        for iteration in range(1, max_iterations + 1):
            print(f"  Iteration {iteration}/{max_iterations}...")

            # Build prompt with spec + context
            prompt = await self._build_iteration_prompt(
                exp_id=exp_id,
                problem=problem,
                spec=spec_result["spec"],
                iteration=iteration,
                checkpoint_guidance=checkpoint_guidance
            )

            # Local model generates solution
            try:
                solution = self.local.generate(prompt, model=local_model)
            except Exception as e:
                print(f"    Error generating solution: {e}")
                await self.cortex.remember(
                    title=f"Experiment {exp_id} - Iteration {iteration} ERROR",
                    content=f"Error during generation: {str(e)}",
                    category="custom",
                    tags=["iteration", "error", exp_id],
                    metadata={
                        "experiment_id": exp_id,
                        "iteration": iteration,
                        "model": local_model,
                        "error": str(e)
                    }
                )
                continue

            # Execute tests
            test_result = execute_solution(solution, problem.get("test", ""))

            # Track local cost (typically $0)
            self.cost_analyzer.add_local_cost(0.0, local_model, "iteration")

            # Store iteration in cortex
            await self.cortex.remember(
                title=f"Experiment {exp_id} - Iteration {iteration}",
                content=f"Code:\n```python\n{solution}\n```\n\nTest Result:\n{test_result}",
                category="custom",
                tags=["iteration", exp_id, f"iter_{iteration}"],
                metadata={
                    "experiment_id": exp_id,
                    "iteration": iteration,
                    "model": local_model,
                    "success": test_result["success"],
                    "error": test_result.get("error"),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Check success
            if test_result["success"]:
                print(f"    ✓ SUCCESS! All tests passed.\n")
                return await self._complete_experiment(
                    exp_id=exp_id,
                    problem_id=problem_id,
                    success=True,
                    iterations=iteration,
                    final_solution=solution
                )
            else:
                error_msg = test_result.get("error", test_result.get("stderr", "Unknown error"))
                print(f"    ✗ Failed: {error_msg[:100]}")

            # Checkpoint every N iterations
            if iteration % self.checkpoint_interval == 0:
                print(f"\n  Checkpoint {iteration // self.checkpoint_interval}...")
                checkpoint_guidance = await self._checkpoint(
                    exp_id=exp_id,
                    iteration=iteration,
                    model=frontier_checkpoint_model
                )
                print(f"    Guidance received from {frontier_checkpoint_model}\n")

        # Max iterations reached without success
        print(f"\n  Max iterations ({max_iterations}) reached without success.\n")
        return await self._complete_experiment(
            exp_id=exp_id,
            problem_id=problem_id,
            success=False,
            iterations=max_iterations,
            final_solution=None
        )

    async def _build_iteration_prompt(
        self,
        exp_id: str,
        problem: dict,
        spec: str,
        iteration: int,
        checkpoint_guidance: Optional[str] = None
    ) -> str:
        """Build prompt for local model iteration.

        Args:
            exp_id: Experiment ID
            problem: Problem dictionary
            spec: Implementation spec
            iteration: Current iteration number
            checkpoint_guidance: Latest checkpoint guidance (if any)

        Returns:
            Prompt string
        """
        # TODO: Query cortex for previous attempts to include in context
        # For MVP, we'll build a basic prompt

        prompt = f"""You are solving a coding problem. Here is the specification:

{spec}

Original Problem:
{problem['prompt']}

"""

        if checkpoint_guidance:
            prompt += f"""
Previous attempts have failed. Here is guidance from a code review:

{checkpoint_guidance}

Take this feedback into account in your solution.

"""

        prompt += """
Generate a complete, working Python solution. Only output the code, no explanations.
"""

        return prompt

    async def _checkpoint(
        self,
        exp_id: str,
        iteration: int,
        model: str
    ) -> Optional[str]:
        """Perform checkpoint review with frontier model.

        Args:
            exp_id: Experiment ID
            iteration: Current iteration
            model: Frontier model to use

        Returns:
            Guidance string from frontier model
        """
        # Query cortex for recent iterations
        # Note: recall returns MCP result, we'll need to parse
        # For MVP, we'll use a simplified approach

        # In production, we'd query the last 5 iterations from cortex
        # For now, placeholder
        recent_iterations = []

        # Generate checkpoint review
        if not recent_iterations:
            # Skip if no iterations to review
            return None

        review_result = self.frontier.checkpoint_review(
            recent_iterations,
            model=model
        )

        self.cost_analyzer.add_frontier_cost(
            review_result["cost"],
            model,
            "checkpoint"
        )

        # Store checkpoint in cortex
        await self.cortex.remember(
            title=f"Experiment {exp_id} - Checkpoint {iteration // self.checkpoint_interval}",
            content=f"Review:\n{review_result['review']}\n\nGuidance:\n{review_result['guidance']}",
            category="learning",
            tags=["checkpoint", exp_id],
            importance="high",
            metadata={
                "experiment_id": exp_id,
                "checkpoint_num": iteration // self.checkpoint_interval,
                "iteration": iteration,
                "model": model,
                "cost": review_result["cost"],
                "timestamp": datetime.now().isoformat()
            }
        )

        return review_result["guidance"]

    async def _complete_experiment(
        self,
        exp_id: str,
        problem_id: str,
        success: bool,
        iterations: int,
        final_solution: Optional[str]
    ) -> dict:
        """Complete experiment and store results.

        Args:
            exp_id: Experiment ID
            problem_id: Problem ID
            success: Whether experiment succeeded
            iterations: Total iterations
            final_solution: Final solution code (if successful)

        Returns:
            Experiment result dictionary
        """
        # Calculate cost analysis
        cost_analysis = self.cost_analyzer.calculate_savings(iterations)

        # Format result content
        result_content = f"""Experiment Complete

Success: {success}
Total Iterations: {iterations}
Problem: {problem_id}

{self.cost_analyzer.format_analysis(iterations)}
"""

        if final_solution:
            result_content += f"\nFinal Solution:\n```python\n{final_solution}\n```"

        # Store final result
        await self.cortex.remember(
            title=f"Experiment {exp_id} - COMPLETED",
            content=result_content,
            category="learning",
            tags=["result", exp_id, problem_id, "completed"],
            importance="high",
            metadata={
                "experiment_id": exp_id,
                "problem_id": problem_id,
                "success": success,
                "iterations": iterations,
                **cost_analysis,
                "timestamp": datetime.now().isoformat()
            }
        )

        # End session (triggers consolidation)
        await self.cortex.end_session()

        # Print summary
        print(f"\n{'='*60}")
        print(f"Experiment Complete: {exp_id}")
        print(f"{'='*60}")
        print(f"Success: {success}")
        print(f"Iterations: {iterations}")
        print(self.cost_analyzer.format_analysis(iterations))

        return {
            "experiment_id": exp_id,
            "problem_id": problem_id,
            "success": success,
            "iterations": iterations,
            "cost_analysis": cost_analysis,
            "final_solution": final_solution
        }
