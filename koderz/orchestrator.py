"""Experiment orchestration logic."""

import uuid
import asyncio
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pathlib import Path

from .cortex.client import CortexClient
from .models.factory import ModelFactory
from .models.registry import get_provider, get_tier, get_spec_guidance
from .benchmarks.humaneval import execute_solution, verify_solution, enhance_test_feedback
from .benchmarks.bigcodebench import execute_bigcodebench_solution, verify_bigcodebench_solution
from .benchmarks.swebench import execute_swebench_solution
from .analysis.cost import CostAnalyzer
from .utils.code_extraction import extract_code, validate_python_syntax, ensure_prompt_imports

if TYPE_CHECKING:
    from .analysis.timing import BenchmarkTimer


class ExperimentOrchestrator:
    """Orchestrates coding experiments with swarm of local + frontier models."""

    def __init__(
        self,
        cortex: CortexClient,
        model_factory: ModelFactory,
        checkpoint_interval: int = 5,
        debug: bool = False,
        debug_dir: str = "./debug",
        test_timeout: int = 10,
        dataset_type: str = "humaneval",
        timer: Optional["BenchmarkTimer"] = None,
        enhanced_feedback: bool = False,
        checkpoint_strategy: str = "fixed",
        cascade_models: Optional[list[str]] = None,
        cascade_budget: int = 2,
        model_aware_specs: bool = False,
        repo_cache_dir: Optional[str] = None
    ):
        """Initialize orchestrator.

        Args:
            cortex: Cortex MCP client
            model_factory: Factory for creating model clients
            checkpoint_interval: Checkpoint every N iterations
            debug: Enable debug mode (save all outputs)
            debug_dir: Directory for debug outputs
            test_timeout: Timeout in seconds for test execution per iteration
            dataset_type: Type of dataset ("humaneval", "bigcodebench", or "swebench")
            timer: Optional BenchmarkTimer for performance instrumentation
            enhanced_feedback: Use structured test feedback instead of raw stderr
            checkpoint_strategy: "fixed" (default) or "on-demand" (trigger on stuck patterns)
            cascade_models: List of models for cascade strategy (e.g., ["gpt-oss:20b-128k", "nemotron-3-nano:30b"])
            cascade_budget: Iterations per model in cascade (default: 2)
            model_aware_specs: Append model-specific guidance to spec generation prompt
            repo_cache_dir: Directory for cached git repos (SWE-bench only)
        """
        self.cortex = cortex
        self.model_factory = model_factory
        self.checkpoint_interval = checkpoint_interval
        self.cost_analyzer = CostAnalyzer()
        self.debug = debug
        self.debug_dir = Path(debug_dir)
        self.test_timeout = test_timeout
        self.dataset_type = dataset_type
        self.timer = timer
        self.enhanced_feedback = enhanced_feedback
        self.checkpoint_strategy = checkpoint_strategy
        self.cascade_models = cascade_models
        self.cascade_budget = cascade_budget
        self.model_aware_specs = model_aware_specs
        self.repo_cache_dir = repo_cache_dir

        # Create debug directory if debug enabled
        if self.debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    def _get_problem_prompt(self, problem: dict) -> str:
        """Get the prompt text from a problem dictionary.

        Handles HumanEval (prompt field), BigCodeBench (complete_prompt field),
        and SWE-bench (problem_statement field).

        Args:
            problem: Problem dictionary

        Returns:
            Prompt text
        """
        if self.dataset_type == "swebench":
            return problem.get("swebench_prompt", problem.get("problem_statement", ""))
        # BigCodeBench uses complete_prompt, HumanEval uses prompt
        return problem.get("prompt", problem.get("complete_prompt", ""))

    def _timed(self, phase_name: str):
        """Get a timing context manager for a phase.

        Args:
            phase_name: Name of the phase to time

        Returns:
            Context manager that times the phase if timer is available,
            otherwise a no-op context manager.
        """
        if self.timer:
            return self.timer.phase(phase_name)
        else:
            # Return a no-op context manager
            from contextlib import nullcontext
            return nullcontext()

    async def run_experiment(
        self,
        problem: dict,
        max_iterations: int = 50,
        local_model: str = "codellama:70b",
        frontier_spec_model: str = "gpt-oss:20b",
        frontier_checkpoint_model: str = "claude-sonnet-4-5",
        reuse_spec: bool = False,
        mode: str = "iterative",
        benchmark_run_id: Optional[str] = None,
        no_spec: bool = False,
        no_checkpoints: bool = False,
        no_cot: bool = False
    ) -> dict:
        """Run a complete experiment on a problem.

        Args:
            problem: HumanEval problem dictionary
            max_iterations: Maximum iterations before giving up
            local_model: Local model to use for iterations
            frontier_spec_model: Model for spec generation (default: gpt-oss:20b)
            frontier_checkpoint_model: Frontier model for checkpoints
            reuse_spec: Reuse existing spec from Cortex instead of regenerating
            mode: Evaluation mode - "zero-shot" or "iterative" (default)
            benchmark_run_id: Optional benchmark run ID to group experiments
            no_spec: Skip spec generation entirely (isolate spec contribution)
            no_checkpoints: Disable checkpoint reviews (isolate checkpoint contribution)
            no_cot: Disable chain-of-thought reasoning in prompts (code only)

        Returns:
            Experiment result dictionary
        """
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        problem_id = problem.get("task_id", "unknown")

        # Store ablation flags for use in _complete_experiment metadata
        self._no_spec = no_spec
        self._no_checkpoints = no_checkpoints
        self._no_cot = no_cot

        print(f"\n{'='*60}")
        print(f"Starting Experiment: {exp_id}")
        print(f"Problem: {problem_id}")
        if benchmark_run_id:
            print(f"Benchmark Run: {benchmark_run_id}")
        print(f"{'='*60}\n")

        # Start session
        with self._timed("cortex_start_session"):
            await self.cortex.start_session(context=f"Experiment {exp_id} - {problem_id}")

        # Phase 1: Generate or reuse spec
        spec_result = None
        spec_reused = False

        if no_spec:
            print("Phase 1: Skipped (no-spec mode)")
            spec_result = {"spec": None, "cost": 0.0}
        elif reuse_spec:
            print(f"Phase 1: Looking for existing spec for {problem_id}...")
            try:
                # Query for spec memories with timeout to avoid hanging
                print("  DEBUG: Querying for spec memories (this may take a moment)...")

                # Use asyncio.wait_for to add timeout
                async def query_specs():
                    arch_memories = await self.cortex.export_memories(
                        tags=["spec", problem_id],
                        category="architecture"
                    )
                    custom_memories = await self.cortex.export_memories(
                        tags=["spec", problem_id],
                        category="custom"
                    )
                    return arch_memories + custom_memories

                # Try with 10 second timeout
                memories = await asyncio.wait_for(query_specs(), timeout=10.0)
                print(f"  DEBUG: Found {len(memories)} memories")

                # Debug: Show what tags we're seeing
                architecture_count = sum(1 for m in memories if m.get('category') == 'architecture')
                print(f"  DEBUG: {architecture_count} architecture memories, {len(memories) - architecture_count} other")

                # Sample a few memory titles and tags for debugging
                for idx, memory in enumerate(memories[:5]):
                    title = memory.get('title', 'No title')[:50]
                    tags = memory.get('tags', [])
                    category = memory.get('category', 'unknown')
                    print(f"  DEBUG: Sample {idx}: category={category}, tags={tags}, title={title}...")

                # Find matching spec
                specs_found = 0
                for idx, memory in enumerate(memories):
                    tags = memory.get("tags", [])
                    has_spec_tag = "spec" in tags
                    has_problem_tag = problem_id in tags

                    if has_spec_tag and has_problem_tag:
                        specs_found += 1
                        # Extract spec from content
                        content = memory.get("content", "")
                        spec_marker = "\n\nSpec:\n"

                        print(f"  DEBUG: Found spec memory {specs_found}:")
                        print(f"    Title: {memory.get('title', 'N/A')}")
                        print(f"    Category: {memory.get('category', 'N/A')}")
                        print(f"    Has spec marker: {spec_marker in content}")

                        if spec_marker in content:
                            spec_text = content.split(spec_marker, 1)[1]
                            spec_result = {
                                "spec": spec_text,
                                "cost": 0.0
                            }
                            spec_reused = True
                            original_model = memory.get("metadata", {}).get("model", "unknown")
                            print(f"  ✓ Found existing spec (generated by {original_model})")
                            print("  Reusing spec (cost: $0.00 - saved!)\n")
                            break
                        else:
                            print("  WARNING: Spec memory found but missing spec marker in content")

                if specs_found == 0:
                    print(f"  DEBUG: No memories found with both 'spec' and '{problem_id}' tags")
                elif not spec_result:
                    print(f"  DEBUG: Found {specs_found} spec memories but none had valid content")

            except asyncio.TimeoutError:
                print("  [WARNING] Cortex query timed out after 10s")
                print("  Will generate new spec instead...\n")
            except Exception as e:
                print(f"  [WARNING] Error querying cortex: {e}")
                print("  Will generate new spec...\n")

            if not spec_result:
                print("  No existing spec found, generating new one...\n")

        # Generate new spec if not reusing or none found
        if not spec_result:
            print(f"Phase 1: Generating spec with {frontier_spec_model}...")
            client = self.model_factory.get_client(frontier_spec_model)

            # Build spec prompt, optionally with model-aware guidance
            spec_prompt = problem["prompt"]
            if self.model_aware_specs:
                guidance = get_spec_guidance(local_model)
                if guidance:
                    spec_prompt += (
                        f"\n\n[MODEL-SPECIFIC GUIDANCE for {local_model}]: {guidance}\n"
                        "Please tailor the specification with this model's strengths "
                        "and weaknesses in mind."
                    )
                    print(f"  [INFO] Model-aware spec guidance appended for {local_model}")

            with self._timed("spec_generation"):
                spec_result = client.generate_spec(
                    spec_prompt,
                    model=frontier_spec_model
                )

            tier = get_tier(frontier_spec_model)
            if tier == "local":
                self.cost_analyzer.add_local_cost(0.0, frontier_spec_model, "spec")
            else:
                self.cost_analyzer.add_frontier_cost(
                    spec_result["cost"],
                    frontier_spec_model,
                    "spec",
                    usage=spec_result.get("usage")
                )

            # Store spec in cortex with critical importance to prevent consolidation
            spec_tags = ["experiment", "spec", exp_id, problem_id]
            if self.model_aware_specs:
                spec_tags.append(f"for_{local_model}")
            if benchmark_run_id:
                spec_tags.append(benchmark_run_id)
            with self._timed("cortex_remember"):
                await self.cortex.remember(
                    title=f"Spec: {exp_id} - {problem_id}",
                    content=f"Experiment ID: {exp_id}\nProblem: {problem_id}\nModel: {frontier_spec_model}\n\n---\n\nProblem:\n{problem['prompt']}\n\nSpec:\n{spec_result['spec']}",
                    category="architecture",  # Use architecture category for better preservation
                    tags=spec_tags,
                    importance="critical",  # Critical importance to prevent consolidation
                    metadata={
                        "experiment_id": exp_id,
                        "problem_id": problem_id,
                        "model": frontier_spec_model,
                        "cost": spec_result["cost"],
                        "timestamp": datetime.now().isoformat()
                    }
                )

            print(f"  Spec generated (cost: ${spec_result['cost']:.4f})")
            print(f"  Stored in cortex with tags: {spec_tags}\n")

        # Phase 2: Execution with local model
        if mode == "zero-shot":
            print(f"Phase 2: Zero-shot execution with {local_model}...")
            print("  (Single attempt, no test feedback)\n")
            return await self._run_zero_shot(
                exp_id, problem, spec_result["spec"], local_model, benchmark_run_id
            )

        # Cascade mode: try multiple models in sequence
        if self.cascade_models:
            print(f"Phase 2: Cascade execution with {' -> '.join(self.cascade_models)}...")
            print(f"  (Budget: {self.cascade_budget} iterations per model)\n")
            return await self._run_cascade(
                exp_id=exp_id,
                problem=problem,
                spec=spec_result["spec"],
                frontier_checkpoint_model=frontier_checkpoint_model,
                benchmark_run_id=benchmark_run_id,
                no_checkpoints=no_checkpoints
            )

        print(f"Phase 2: Iterative execution with {local_model}...")
        print("  (Mode: iterative with test feedback)\n")
        if no_checkpoints:
            print("  [INFO] Checkpoints disabled")
        if self.checkpoint_strategy == "on-demand":
            print("  [INFO] On-demand checkpoint strategy enabled")
        if self.enhanced_feedback:
            print("  [INFO] Enhanced test feedback enabled")

        checkpoint_guidance = None
        previous_error = None
        previous_code = None
        # Track iteration history for on-demand checkpoint detection
        recent_pass_rates: list[float] = []
        recent_errors: list[str] = []

        for iteration in range(1, max_iterations + 1):
            print(f"  Iteration {iteration}/{max_iterations}...")

            # Show context being provided
            if iteration > 1 and previous_error:
                print("    [FEEDBACK] Including previous error in prompt")
            if checkpoint_guidance:
                print("    [GUIDANCE] Including checkpoint guidance in prompt")

            # Build prompt with spec + context + previous error/code
            system_prompt, user_prompt = await self._build_iteration_prompt(
                exp_id=exp_id,
                problem=problem,
                spec=spec_result["spec"],
                iteration=iteration,
                checkpoint_guidance=checkpoint_guidance,
                previous_error=previous_error,
                previous_code=previous_code
            )

            # Generate solution with specified model
            try:
                client = self.model_factory.get_client(local_model)
                provider = get_provider(local_model)

                # For local models (Ollama):
                iter_usage = None
                with self._timed("iteration_generate"):
                    if provider == "ollama":
                        raw_output = client.generate(user_prompt, model=local_model, system=system_prompt)
                        cost = 0.0
                    # For API models:
                    else:
                        result = client.generate(user_prompt, model=local_model, system=system_prompt)
                        raw_output = result["text"]
                        cost = result["cost"]
                        iter_usage = result.get("usage")

                # Save raw output if debug enabled
                if self.debug:
                    raw_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_raw.txt"
                    raw_file.write_text(raw_output)
                    print(f"    [DEBUG] Raw output saved to {raw_file}")

                # Extract executable code from model response
                # SWE-bench: skip code extraction, pass raw output to evaluator
                if self.dataset_type == "swebench":
                    solution = raw_output
                else:
                    solution = extract_code(raw_output)

                    # Check if extraction modified the output
                    if solution != raw_output:
                        print("    [INFO] Code extracted from markdown/text wrapper")

                    # Restore imports from the problem prompt that the model may have dropped
                    prompt_text = problem.get("prompt", problem.get("complete_prompt", ""))
                    if prompt_text:
                        solution = ensure_prompt_imports(solution, prompt_text)

                    # Validate syntax
                    is_valid, error_msg = validate_python_syntax(solution)
                    if not is_valid:
                        print(f"    [WARNING] Invalid Python syntax: {error_msg}")
                        # Try using raw output as fallback
                        if solution != raw_output:
                            print("    [WARNING] Attempting with raw output instead")
                            solution = raw_output

                # Save extracted code if debug enabled
                if self.debug:
                    code_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_code.py"
                    code_file.write_text(solution)
                    print(f"    [DEBUG] Extracted code saved to {code_file}")

                    # Show first few lines of code
                    code_lines = solution.split('\n')[:3]
                    print(f"    [DEBUG] Code preview: {code_lines[0][:60]}...")

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

            # Execute tests - use appropriate function based on dataset type
            with self._timed("iteration_test"):
                if self.dataset_type == "swebench":
                    test_result = execute_swebench_solution(
                        problem, solution, self.repo_cache_dir, self.test_timeout
                    )
                elif self.dataset_type == "bigcodebench":
                    test_result = execute_bigcodebench_solution(
                        solution,
                        problem.get("test", ""),
                        entry_point=problem.get("entry_point", ""),
                        timeout=self.test_timeout,
                        libs=problem.get("libs", [])
                    )
                else:
                    test_result = execute_solution(
                        solution,
                        problem.get("test", ""),
                        entry_point=problem.get("entry_point", ""),
                        timeout=self.test_timeout
                    )

            # Save test result if debug enabled
            if self.debug:
                result_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_result.txt"
                result_content = f"Success: {test_result['success']}\n"
                result_content += f"Tests: {test_result.get('tests_passed', 0)}/{test_result.get('tests_total', 0)}\n"
                result_content += f"Test Pass Rate: {test_result.get('test_pass_rate', 0.0):.1%}\n"
                result_content += f"Error: {test_result.get('error', 'None')}\n"
                result_content += f"Stdout: {test_result.get('stdout', '')}\n"
                result_content += f"Stderr: {test_result.get('stderr', '')}\n"
                result_file.write_text(result_content)
                print(f"    [DEBUG] Test result saved to {result_file}")

            # Track cost with tier info
            tier = get_tier(local_model)
            if tier == "local":
                self.cost_analyzer.add_local_cost(0.0, local_model, "iteration")
            else:
                self.cost_analyzer.add_frontier_cost(cost, local_model, "iteration", usage=iter_usage)

            # Store iteration in cortex with structured data
            iter_tags = ["iteration", exp_id, f"iter_{iteration}"]
            if benchmark_run_id:
                iter_tags.append(benchmark_run_id)
            with self._timed("cortex_remember"):
                await self.cortex.remember(
                    title=f"Experiment {exp_id} - Iteration {iteration}",
                    content=solution,  # Store just the code for easy extraction
                    category="custom",
                    tags=iter_tags,
                    importance="high",  # Prevent consolidation - needed for analysis
                    metadata={
                        "experiment_id": exp_id,
                        "iteration": iteration,
                        "model": local_model,
                        "success": test_result["success"],
                        "tests_passed": test_result.get("tests_passed", 0),
                        "tests_total": test_result.get("tests_total", 0),
                        "test_pass_rate": test_result.get("test_pass_rate", 0.0),
                        "error": test_result.get("error", ""),
                        "stderr": test_result.get("stderr", ""),
                        "stdout": test_result.get("stdout", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # Check success
            if test_result["success"]:
                tests_passed = test_result.get("tests_passed", 0)
                tests_total = test_result.get("tests_total", 0)
                print(f"    ✓ SUCCESS! All {tests_total} tests passed.\n")
                return await self._complete_experiment(
                    exp_id=exp_id,
                    problem_id=problem_id,
                    success=True,
                    iterations=iteration,
                    final_solution=solution,
                    mode="iterative",
                    benchmark_run_id=benchmark_run_id
                )
            else:
                error_msg = test_result.get("error", test_result.get("stderr", "Unknown error"))
                tests_passed = test_result.get("tests_passed", 0)
                tests_total = test_result.get("tests_total", 0)
                test_pass_rate = test_result.get("test_pass_rate", 0.0)
                print(f"    ✗ Failed: {tests_passed}/{tests_total} tests ({test_pass_rate:.0%}) - {error_msg[:80]}")

                # Enhanced feedback: parse raw error into structured format
                if self.enhanced_feedback and error_msg:
                    test_code = problem.get("test", "")
                    enhanced_error = enhance_test_feedback(error_msg, solution, test_code)
                    previous_error = enhanced_error
                    if self.debug:
                        print(f"    [ENHANCED FEEDBACK]\n{enhanced_error}")
                else:
                    previous_error = error_msg
                previous_code = solution

                # Track history for on-demand checkpoint detection
                recent_pass_rates.append(test_pass_rate)
                recent_errors.append(error_msg[:200] if error_msg else "")

            # Checkpoint logic
            should_checkpoint = False
            if not no_checkpoints:
                if self.checkpoint_strategy == "on-demand":
                    should_checkpoint = self._detect_stuck_pattern(
                        recent_pass_rates, recent_errors, iteration
                    )
                    if should_checkpoint:
                        print("    [ON-DEMAND] Stuck pattern detected, triggering checkpoint")
                else:
                    # Fixed strategy: checkpoint at every N iterations
                    should_checkpoint = iteration % self.checkpoint_interval == 0

            if should_checkpoint:
                cp_num = iteration // self.checkpoint_interval if self.checkpoint_strategy == "fixed" else len([r for r in recent_pass_rates]) // 3
                print(f"\n  Checkpoint (iter {iteration})...")
                with self._timed("checkpoint_review"):
                    checkpoint_guidance = await self._checkpoint(
                        exp_id=exp_id,
                        iteration=iteration,
                        model=frontier_checkpoint_model,
                        problem_prompt=problem["prompt"]
                    )
                print(f"    Guidance received from {frontier_checkpoint_model}\n")

        # Max iterations reached without success
        print(f"\n  Max iterations ({max_iterations}) reached without success.\n")
        return await self._complete_experiment(
            exp_id=exp_id,
            problem_id=problem_id,
            success=False,
            iterations=max_iterations,
            final_solution=None,
            mode="iterative",
            benchmark_run_id=benchmark_run_id
        )

    @staticmethod
    def _detect_stuck_pattern(
        recent_pass_rates: list[float],
        recent_errors: list[str],
        iteration: int
    ) -> bool:
        """Detect if the model is stuck and needs a checkpoint.

        Checks for three patterns:
        - Plateau: Same test_pass_rate for 3+ consecutive failed iterations
        - Oscillation: Error alternates between 2 values over 4+ iterations
        - Zero progress: 0 tests passing for 3+ consecutive iterations

        Args:
            recent_pass_rates: List of test pass rates from failed iterations
            recent_errors: List of error messages from failed iterations
            iteration: Current iteration number

        Returns:
            True if a stuck pattern is detected
        """
        n = len(recent_pass_rates)
        if n < 3:
            return False

        # Plateau: same pass rate for last 3 iterations
        last3 = recent_pass_rates[-3:]
        if last3[0] == last3[1] == last3[2]:
            return True

        # Zero progress: 0% for last 3 iterations
        if all(r == 0.0 for r in last3):
            return True

        # Oscillation: error alternates between 2 values over last 4 iterations
        if n >= 4:
            last4_errors = recent_errors[-4:]
            if (last4_errors[0] == last4_errors[2] and
                last4_errors[1] == last4_errors[3] and
                last4_errors[0] != last4_errors[1]):
                return True

        return False

    async def _run_cascade(
        self,
        exp_id: str,
        problem: dict,
        spec: Optional[str],
        frontier_checkpoint_model: str,
        benchmark_run_id: Optional[str] = None,
        no_checkpoints: bool = False
    ) -> dict:
        """Run cascade strategy: try multiple models in sequence.

        Each model gets cascade_budget iterations. Error context carries across
        model boundaries so later models see what was tried.

        Args:
            exp_id: Experiment ID
            problem: Problem dictionary
            spec: Implementation specification
            frontier_checkpoint_model: Model for checkpoint reviews
            benchmark_run_id: Optional benchmark run ID
            no_checkpoints: Whether to disable checkpoints

        Returns:
            Experiment result dictionary
        """
        problem_id = problem.get("task_id", "unknown")
        previous_error = None
        previous_code = None
        checkpoint_guidance = None
        total_iterations = 0

        for model_idx, cascade_model in enumerate(self.cascade_models):
            print(f"\n  Cascade stage {model_idx + 1}/{len(self.cascade_models)}: {cascade_model}")

            for budget_iter in range(1, self.cascade_budget + 1):
                total_iterations += 1
                iteration = total_iterations
                print(f"    Iteration {iteration} (model: {cascade_model}, budget {budget_iter}/{self.cascade_budget})...")

                # Build prompt with carried context
                system_prompt, user_prompt = await self._build_iteration_prompt(
                    exp_id=exp_id,
                    problem=problem,
                    spec=spec,
                    iteration=iteration,
                    checkpoint_guidance=checkpoint_guidance,
                    previous_error=previous_error,
                    previous_code=previous_code
                )

                # Generate solution
                try:
                    client = self.model_factory.get_client(cascade_model)
                    provider = get_provider(cascade_model)

                    iter_usage = None
                    with self._timed("iteration_generate"):
                        if provider == "ollama":
                            raw_output = client.generate(user_prompt, model=cascade_model, system=system_prompt)
                            cost = 0.0
                        else:
                            result = client.generate(user_prompt, model=cascade_model, system=system_prompt)
                            raw_output = result["text"]
                            cost = result["cost"]
                            iter_usage = result.get("usage")

                    # Debug output
                    if self.debug:
                        raw_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_raw.txt"
                        raw_file.write_text(raw_output)

                    # Extract and validate code
                    if self.dataset_type == "swebench":
                        solution = raw_output
                    else:
                        solution = extract_code(raw_output)
                        prompt_text = problem.get("prompt", problem.get("complete_prompt", ""))
                        if prompt_text:
                            solution = ensure_prompt_imports(solution, prompt_text)
                        is_valid, error_msg = validate_python_syntax(solution)
                        if not is_valid and solution != raw_output:
                            solution = raw_output

                    if self.debug:
                        code_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_code.py"
                        code_file.write_text(solution)

                except Exception as e:
                    print(f"      Error generating solution: {e}")
                    continue

                # Execute tests
                with self._timed("iteration_test"):
                    if self.dataset_type == "swebench":
                        test_result = execute_swebench_solution(
                            problem, solution, self.repo_cache_dir, self.test_timeout
                        )
                    elif self.dataset_type == "bigcodebench":
                        test_result = execute_bigcodebench_solution(
                            solution,
                            problem.get("test", ""),
                            entry_point=problem.get("entry_point", ""),
                            timeout=self.test_timeout,
                            libs=problem.get("libs", [])
                        )
                    else:
                        test_result = execute_solution(
                            solution,
                            problem.get("test", ""),
                            entry_point=problem.get("entry_point", ""),
                            timeout=self.test_timeout
                        )

                # Debug output
                if self.debug:
                    result_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_result.txt"
                    result_content = f"Success: {test_result['success']}\n"
                    result_content += f"Tests: {test_result.get('tests_passed', 0)}/{test_result.get('tests_total', 0)}\n"
                    result_content += f"Model: {cascade_model}\n"
                    result_content += f"Error: {test_result.get('error', 'None')}\n"
                    result_file.write_text(result_content)

                # Track cost attributed to the correct model
                tier = get_tier(cascade_model)
                if tier == "local":
                    self.cost_analyzer.add_local_cost(0.0, cascade_model, "iteration")
                else:
                    self.cost_analyzer.add_frontier_cost(cost, cascade_model, "iteration", usage=iter_usage)

                # Store iteration in cortex
                iter_tags = ["iteration", exp_id, f"iter_{iteration}", f"cascade_{cascade_model}"]
                if benchmark_run_id:
                    iter_tags.append(benchmark_run_id)
                with self._timed("cortex_remember"):
                    await self.cortex.remember(
                        title=f"Experiment {exp_id} - Iteration {iteration}",
                        content=solution,
                        category="custom",
                        tags=iter_tags,
                        importance="high",
                        metadata={
                            "experiment_id": exp_id,
                            "iteration": iteration,
                            "model": cascade_model,
                            "cascade_stage": model_idx + 1,
                            "success": test_result["success"],
                            "tests_passed": test_result.get("tests_passed", 0),
                            "tests_total": test_result.get("tests_total", 0),
                            "test_pass_rate": test_result.get("test_pass_rate", 0.0),
                            "error": test_result.get("error", ""),
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                # Check success
                if test_result["success"]:
                    tests_total = test_result.get("tests_total", 0)
                    print(f"      ✓ SUCCESS! All {tests_total} tests passed (model: {cascade_model}).\n")
                    return await self._complete_experiment(
                        exp_id=exp_id,
                        problem_id=problem_id,
                        success=True,
                        iterations=total_iterations,
                        final_solution=solution,
                        mode="cascade",
                        benchmark_run_id=benchmark_run_id
                    )
                else:
                    err = test_result.get("error", "Unknown error")
                    tests_passed = test_result.get("tests_passed", 0)
                    tests_total = test_result.get("tests_total", 0)
                    test_pass_rate = test_result.get("test_pass_rate", 0.0)
                    print(f"      ✗ Failed: {tests_passed}/{tests_total} ({test_pass_rate:.0%}) - {err[:60]}")

                    # Enhanced feedback
                    if self.enhanced_feedback and err:
                        test_code = problem.get("test", "")
                        previous_error = enhance_test_feedback(err, solution, test_code)
                    else:
                        previous_error = err
                    previous_code = solution

            # Model exhausted its budget, carry context to next model
            print(f"    Model {cascade_model} exhausted budget ({self.cascade_budget} iterations)")

        # All models exhausted - optionally fire checkpoint and retry with first model
        if not no_checkpoints:
            print("\n  All cascade models exhausted. Firing checkpoint for recovery...")
            with self._timed("checkpoint_review"):
                checkpoint_guidance = await self._checkpoint(
                    exp_id=exp_id,
                    iteration=total_iterations,
                    model=frontier_checkpoint_model,
                    problem_prompt=problem["prompt"]
                )
            print(f"    Guidance received from {frontier_checkpoint_model}")

            # Retry with first cascade model using checkpoint guidance
            first_model = self.cascade_models[0]
            print(f"  Retrying with {first_model} + checkpoint guidance ({self.cascade_budget} iterations)...")

            for retry_iter in range(1, self.cascade_budget + 1):
                total_iterations += 1
                iteration = total_iterations
                print(f"    Iteration {iteration} (post-checkpoint retry {retry_iter}/{self.cascade_budget})...")

                system_prompt, user_prompt = await self._build_iteration_prompt(
                    exp_id=exp_id,
                    problem=problem,
                    spec=spec,
                    iteration=iteration,
                    checkpoint_guidance=checkpoint_guidance,
                    previous_error=previous_error,
                    previous_code=previous_code
                )

                try:
                    client = self.model_factory.get_client(first_model)
                    provider = get_provider(first_model)

                    iter_usage = None
                    with self._timed("iteration_generate"):
                        if provider == "ollama":
                            raw_output = client.generate(user_prompt, model=first_model, system=system_prompt)
                            cost = 0.0
                        else:
                            result = client.generate(user_prompt, model=first_model, system=system_prompt)
                            raw_output = result["text"]
                            cost = result["cost"]
                            iter_usage = result.get("usage")

                    if self.dataset_type == "swebench":
                        solution = raw_output
                    else:
                        solution = extract_code(raw_output)
                        prompt_text = problem.get("prompt", problem.get("complete_prompt", ""))
                        if prompt_text:
                            solution = ensure_prompt_imports(solution, prompt_text)

                    if self.debug:
                        code_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_code.py"
                        code_file.write_text(solution)

                except Exception as e:
                    print(f"      Error: {e}")
                    continue

                with self._timed("iteration_test"):
                    if self.dataset_type == "swebench":
                        test_result = execute_swebench_solution(
                            problem, solution, self.repo_cache_dir, self.test_timeout
                        )
                    elif self.dataset_type == "bigcodebench":
                        test_result = execute_bigcodebench_solution(
                            solution, problem.get("test", ""),
                            entry_point=problem.get("entry_point", ""),
                            timeout=self.test_timeout, libs=problem.get("libs", [])
                        )
                    else:
                        test_result = execute_solution(
                            solution, problem.get("test", ""),
                            entry_point=problem.get("entry_point", ""),
                            timeout=self.test_timeout
                        )

                tier = get_tier(first_model)
                if tier == "local":
                    self.cost_analyzer.add_local_cost(0.0, first_model, "iteration")
                else:
                    self.cost_analyzer.add_frontier_cost(cost, first_model, "iteration", usage=iter_usage)

                if test_result["success"]:
                    tests_total = test_result.get("tests_total", 0)
                    print(f"      ✓ SUCCESS! All {tests_total} tests passed (post-checkpoint retry).\n")
                    return await self._complete_experiment(
                        exp_id=exp_id, problem_id=problem_id, success=True,
                        iterations=total_iterations, final_solution=solution,
                        mode="cascade", benchmark_run_id=benchmark_run_id
                    )
                else:
                    err = test_result.get("error", "Unknown error")
                    print(f"      ✗ Failed: {err[:60]}")
                    if self.enhanced_feedback and err:
                        previous_error = enhance_test_feedback(err, solution, problem.get("test", ""))
                    else:
                        previous_error = err
                    previous_code = solution

        # All cascade attempts exhausted
        print(f"\n  Cascade exhausted ({total_iterations} total iterations).\n")
        return await self._complete_experiment(
            exp_id=exp_id, problem_id=problem_id, success=False,
            iterations=total_iterations, final_solution=None,
            mode="cascade", benchmark_run_id=benchmark_run_id
        )

    async def _run_zero_shot(
        self,
        exp_id: str,
        problem: dict,
        spec: str,
        local_model: str,
        benchmark_run_id: Optional[str] = None
    ) -> dict:
        """Run zero-shot evaluation (single attempt, no feedback).

        Args:
            exp_id: Experiment ID
            problem: Problem dictionary
            spec: Implementation specification
            local_model: Model to use
            benchmark_run_id: Optional benchmark run ID to group experiments

        Returns:
            Experiment result dictionary
        """
        problem_id = problem.get("task_id", "unknown")

        # Build zero-shot prompt (no error feedback, no guidance)
        system_prompt, user_prompt = await self._build_zero_shot_prompt(
            problem=problem,
            spec=spec,
            no_cot=self._no_cot
        )

        # Generate solution (single attempt)
        print("  Generating solution...")
        client = self.model_factory.get_client(local_model)
        provider = get_provider(local_model)
        tier = get_tier(local_model)

        zs_usage = None
        with self._timed("iteration_generate"):
            if provider == "ollama":
                solution = client.generate(user_prompt, model=local_model, system=system_prompt)
                cost = 0.0
            else:
                result = client.generate(user_prompt, model=local_model, system=system_prompt)
                solution = result["text"]
                cost = result["cost"]
                zs_usage = result.get("usage")

        # Track cost
        if tier == "local":
            self.cost_analyzer.add_local_cost(0.0, local_model, "iteration")
        else:
            self.cost_analyzer.add_frontier_cost(cost, local_model, "iteration", usage=zs_usage)

        # Debug: save raw output
        if self.debug:
            raw_file = self.debug_dir / f"{exp_id}_zeroshot_raw.txt"
            raw_file.write_text(solution)
            print(f"    [DEBUG] Raw output saved to {raw_file}")

        # Extract code — SWE-bench: skip extraction, pass raw output
        if self.dataset_type == "swebench":
            code = solution
        else:
            code = extract_code(solution)
            print("    [INFO] Code extracted from markdown/text wrapper")

            # Restore imports from the problem prompt that the model may have dropped
            prompt_text = problem.get("prompt", problem.get("complete_prompt", ""))
            if prompt_text:
                code = ensure_prompt_imports(code, prompt_text)

        # Debug: save extracted code
        if self.debug:
            code_file = self.debug_dir / f"{exp_id}_zeroshot_code.py"
            code_file.write_text(code)
            print(f"    [DEBUG] Extracted code saved to {code_file}")

        if self.dataset_type == "swebench":
            # SWE-bench: run full evaluation pipeline
            print("    Executing SWE-bench evaluation...")
            with self._timed("iteration_test"):
                result = execute_swebench_solution(
                    problem, code, self.repo_cache_dir, self.test_timeout
                )
        else:
            # Validate syntax
            is_valid, syntax_error = validate_python_syntax(code)
            if not is_valid:
                print(f"    ✗ Syntax error: {syntax_error}")
                result = {
                    "success": False,
                    "error": f"SyntaxError: {syntax_error}",
                    "stdout": "",
                    "stderr": f"SyntaxError: {syntax_error}"
                }
            else:
                # Execute tests - use appropriate function based on dataset type
                print("    Executing tests...")
                with self._timed("iteration_test"):
                    if self.dataset_type == "bigcodebench":
                        result = verify_bigcodebench_solution(problem, code, timeout=self.test_timeout)
                    else:
                        result = verify_solution(problem, code, timeout=self.test_timeout)

        # Debug: save result
        if self.debug:
            result_file = self.debug_dir / f"{exp_id}_zeroshot_result.txt"
            result_text = f"Success: {result['success']}\n"
            result_text += f"Tests: {result.get('tests_passed', 0)}/{result.get('tests_total', 0)}\n"
            result_text += f"Test Pass Rate: {result.get('test_pass_rate', 0.0):.1%}\n"
            result_text += f"Error: {result.get('error', '')}\n"
            result_text += f"Stdout: {result.get('stdout', '')}\n"
            result_text += f"Stderr: {result.get('stderr', '')}\n"
            result_file.write_text(result_text)
            print(f"    [DEBUG] Test result saved to {result_file}")

        # Report result
        tests_passed = result.get("tests_passed", 0)
        tests_total = result.get("tests_total", 0)
        test_pass_rate = result.get("test_pass_rate", 0.0)

        if result["success"]:
            print(f"    ✓ Success on first attempt! All {tests_total} tests passed.\n")
            return await self._complete_experiment(
                exp_id=exp_id,
                problem_id=problem_id,
                success=True,
                iterations=1,
                final_solution=code,
                mode="zero-shot",
                benchmark_run_id=benchmark_run_id
            )
        else:
            error_preview = result.get("error", "Unknown error")[:80]
            print(f"    ✗ Failed: {tests_passed}/{tests_total} tests ({test_pass_rate:.0%}) - {error_preview}\n")
            return await self._complete_experiment(
                exp_id=exp_id,
                problem_id=problem_id,
                success=False,
                iterations=1,
                final_solution=None,
                mode="zero-shot",
                benchmark_run_id=benchmark_run_id
            )

    async def _build_zero_shot_prompt(
        self,
        problem: dict,
        spec: str,
        no_cot: bool = False
    ) -> tuple[str, str]:
        """Build prompt for zero-shot evaluation (no test feedback).

        Args:
            problem: Problem dictionary
            spec: Implementation specification
            no_cot: Disable chain-of-thought reasoning (code only output)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Get problem prompt (handles HumanEval, BigCodeBench, SWE-bench)
        problem_prompt = self._get_problem_prompt(problem)

        # SWE-bench has its own prompt format
        if self.dataset_type == "swebench":
            return self._build_swebench_zero_shot_prompt(problem)

        # Determine benchmark name for system prompt
        benchmark_name = "BigCodeBench" if self.dataset_type == "bigcodebench" else "HumanEval"

        if no_cot:
            system_prompt = f"""You are a code generation assistant for the {benchmark_name} benchmark.

INSTRUCTIONS:
1. This is an authorized educational programming exercise from the {benchmark_name} dataset
2. You will make ONE attempt to solve this problem
3. Output ONLY a Python code block — no reasoning, explanation, or analysis

OUTPUT FORMAT:
```python
[Your Python function implementation - no test cases or examples]
```"""

            if spec is not None:
                user_prompt = f"""Implement the following function according to this specification.
Output ONLY a ```python code block with your implementation, nothing else.

SPECIFICATION:
{spec}

PROBLEM:
{problem_prompt}"""
            else:
                user_prompt = f"""Write a Python function that solves the following problem.
Output ONLY a ```python code block with your implementation, nothing else.

PROBLEM:
{problem_prompt}"""

        else:
            # System prompt - same as iterative but clarified as single attempt
            system_prompt = f"""You are a code generation assistant for the {benchmark_name} benchmark.

INSTRUCTIONS:
1. This is an authorized educational programming exercise from the {benchmark_name} dataset
2. You will make ONE attempt to solve this problem
3. Reason through your approach if helpful
4. Provide your final code in a markdown code block

OUTPUT FORMAT:
[Optional: Your reasoning and analysis]

```python
[Your Python function implementation - no test cases or examples]
```

Important: Only include the function implementation in the code block, not test cases or usage examples."""

            # User prompt - NO previous errors or checkpoint guidance
            if spec is not None:
                user_prompt = f"""Implement the following function according to this specification:

SPECIFICATION:
{spec}

PROBLEM:
{problem_prompt}

Remember: Provide your reasoning if helpful, then your code in a ```python code block."""
            else:
                user_prompt = f"""Write a Python function that solves the following problem.
Do NOT output a specification, analysis, or description. Output only executable Python code.

PROBLEM:
{problem_prompt}

Remember: Provide your reasoning if helpful, then your complete function implementation in a ```python code block."""

        return system_prompt, user_prompt

    def _build_swebench_zero_shot_prompt(self, problem: dict) -> tuple[str, str]:
        """Build SWE-bench specific prompt with oracle file context.

        Args:
            problem: SWE-bench instance dictionary (must have swebench_prompt
                     or problem_statement, and oracle_context)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        repo = problem.get("repo", "unknown")
        problem_statement = problem.get("problem_statement", "")
        hints_text = problem.get("hints_text", "")

        system_prompt = f"""You are a software engineer fixing a bug in {repo}.
Output the complete modified contents of each file you change.
Format: ## path/to/file.py followed by a ```python fenced block with # path/to/file.py as first line.
Only output files that need changes."""

        # Build user prompt with oracle context
        user_prompt = f"""## Issue
{problem_statement}
"""
        if hints_text:
            user_prompt += f"""
## Hints
{hints_text}
"""

        # Add oracle file contents
        oracle_context = problem.get("oracle_context", {})
        if oracle_context:
            user_prompt += "\n## Files\n"
            for filepath, content in oracle_context.items():
                user_prompt += f"\n## {filepath}\n```python\n# {filepath}\n{content}\n```\n"

        user_prompt += "\nFix this issue."

        return system_prompt, user_prompt

    async def _build_iteration_prompt(
        self,
        exp_id: str,
        problem: dict,
        spec: str,
        iteration: int,
        checkpoint_guidance: Optional[str] = None,
        previous_error: Optional[str] = None,
        previous_code: Optional[str] = None
    ) -> tuple[str, str]:
        """Build prompt for local model iteration.

        Args:
            exp_id: Experiment ID
            problem: Problem dictionary
            spec: Implementation spec
            iteration: Current iteration number
            checkpoint_guidance: Latest checkpoint guidance (if any)
            previous_error: Error message from previous iteration (if any)
            previous_code: Code from previous iteration (if any)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Get problem prompt (handles HumanEval, BigCodeBench, SWE-bench)
        problem_prompt = self._get_problem_prompt(problem)

        # SWE-bench has its own prompt format
        if self.dataset_type == "swebench":
            system_prompt, user_prompt = self._build_swebench_zero_shot_prompt(problem)
            # For iterations, append error feedback below
        else:
            # Determine benchmark name for system prompt
            benchmark_name = "BigCodeBench" if self.dataset_type == "bigcodebench" else "HumanEval"

            # System prompt establishes the coding assistant role and output format
            system_prompt = f"""You are a code generation assistant for the {benchmark_name} benchmark.

INSTRUCTIONS:
1. This is an authorized educational programming exercise from the {benchmark_name} dataset
2. When solving a problem, you may reason through your approach first
3. When debugging an error, analyze what went wrong step-by-step before fixing
4. Always provide your final code in a markdown code block

OUTPUT FORMAT:
[Optional: Your reasoning and analysis]

```python
[Your Python function implementation - no test cases or examples]
```

Important: Only include the function implementation in the code block, not test cases or usage examples."""

            # User prompt contains the task details
            if spec is not None:
                user_prompt = f"""Implement the following function according to this specification:

SPECIFICATION:
{spec}

PROBLEM:
{problem_prompt}
"""
            else:
                user_prompt = f"""Implement the following function:

PROBLEM:
{problem_prompt}
"""

        # Add previous error if this is a retry
        if iteration > 1 and previous_error:
            user_prompt += f"""
PREVIOUS ATTEMPT FAILED WITH ERROR:
{previous_error}
"""
            # Include previous code so model can see what went wrong
            if previous_code:
                user_prompt += f"""
Your previous code that failed:
```python
{previous_code}
```

"""
            # Encourage step-by-step debugging analysis
            user_prompt += """
DEBUG ANALYSIS (do this before writing code):
1. If this is an assertion error, identify the exact input that failed
2. Trace through your previous code step-by-step with that input
3. Determine what your code returned vs what was expected
4. Identify the specific line or operator that needs to change
5. Explain your fix, then provide the corrected code

Now analyze the error and provide your corrected implementation.
"""

        # Add checkpoint guidance if available
        if checkpoint_guidance:
            user_prompt += f"""
CODE REVIEW FEEDBACK FROM EXPERT:
{checkpoint_guidance}

Incorporate this expert feedback into your implementation.
"""

        user_prompt += """
Remember: Provide your reasoning if helpful, then your code in a ```python code block."""

        return system_prompt, user_prompt

    def _parse_result_file(self, result_text: str) -> dict:
        """Parse result file to extract metadata.

        Args:
            result_text: Content of result file

        Returns:
            Dictionary with success, error, stdout, stderr
        """
        metadata = {
            'success': False,
            'error': '',
            'stdout': '',
            'stderr': ''
        }

        lines = result_text.split('\n')
        current_section = None

        for line in lines:
            if line.startswith('Success: '):
                metadata['success'] = line.split('Success: ')[1].strip() == 'True'
            elif line.startswith('Error: '):
                current_section = 'error'
                metadata['error'] = line.split('Error: ', 1)[1] if len(line.split('Error: ', 1)) > 1 else ''
            elif line.startswith('Stdout: '):
                current_section = 'stdout'
                metadata['stdout'] = line.split('Stdout: ', 1)[1] if len(line.split('Stdout: ', 1)) > 1 else ''
            elif line.startswith('Stderr: '):
                current_section = 'stderr'
                metadata['stderr'] = line.split('Stderr: ', 1)[1] if len(line.split('Stderr: ', 1)) > 1 else ''
            elif current_section and line.strip():
                # Continuation of multi-line section
                metadata[current_section] += '\n' + line

        return metadata

    async def _checkpoint(
        self,
        exp_id: str,
        iteration: int,
        model: str,
        problem_prompt: str
    ) -> Optional[str]:
        """Perform checkpoint review with frontier model.

        Args:
            exp_id: Experiment ID
            iteration: Current iteration
            model: Frontier model to use
            problem_prompt: Original problem prompt for progressive spec

        Returns:
            Guidance string from frontier model
        """
        # Read ALL iterations from debug files (more reliable than Cortex query)
        # Full history lets the checkpoint model detect cycles and avoid repeated approaches
        start_iter = 1

        recent_iterations = []
        for iter_num in range(start_iter, iteration + 1):
            try:
                # Read from debug files if available
                if self.debug:
                    code_file = self.debug_dir / f"{exp_id}_iter{iter_num:03d}_code.py"
                    result_file = self.debug_dir / f"{exp_id}_iter{iter_num:03d}_result.txt"

                    if code_file.exists() and result_file.exists():
                        code = code_file.read_text()
                        result_text = result_file.read_text()

                        # Parse result file to extract metadata
                        metadata = self._parse_result_file(result_text)

                        recent_iterations.append({
                            'iteration': iter_num,
                            'content': code,
                            'metadata': metadata
                        })
                    else:
                        print(f"    [WARNING] Debug files missing for iteration {iter_num}")
                else:
                    # Fallback to Cortex query if debug mode not enabled
                    memories = await self.cortex.export_memories(
                        tags=["iteration", exp_id, f"iter_{iter_num}"]
                    )

                    if memories:
                        memory = memories[0]
                        recent_iterations.append({
                            'iteration': iter_num,
                            'content': memory.get('content', ''),
                            'metadata': memory.get('metadata', {})
                        })
            except Exception as e:
                print(f"    [WARNING] Could not retrieve iteration {iter_num}: {e}")
                continue

        # Generate checkpoint review
        if not recent_iterations:
            print(f"    [WARNING] No iterations found to review (checked {start_iter}-{iteration})")
            return None

        print(f"    Reviewing {len(recent_iterations)}/{iteration} iterations (full history)")

        checkpoint_num = iteration // self.checkpoint_interval
        client = self.model_factory.get_client(model)
        review_result = client.checkpoint_review(
            recent_iterations,
            model=model,
            checkpoint_num=checkpoint_num,
            problem_prompt=problem_prompt
        )

        tier = get_tier(model)
        if tier == "local":
            self.cost_analyzer.add_local_cost(0.0, model, "checkpoint")
        else:
            self.cost_analyzer.add_frontier_cost(
                review_result["cost"],
                model,
                "checkpoint",
                usage=review_result.get("usage")
            )

        # Store checkpoint in cortex
        with self._timed("cortex_remember"):
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

        # Save checkpoint guidance if debug enabled
        if self.debug:
            checkpoint_num = iteration // self.checkpoint_interval
            checkpoint_file = self.debug_dir / f"{exp_id}_checkpoint{checkpoint_num:02d}_guidance.txt"
            checkpoint_content = f"Checkpoint {checkpoint_num} at Iteration {iteration}\n"
            checkpoint_content += f"Model: {model}\n\n"
            checkpoint_content += f"Review:\n{review_result['review']}\n\n"
            checkpoint_content += f"Guidance:\n{review_result['guidance']}\n"
            checkpoint_file.write_text(checkpoint_content)
            print(f"    [DEBUG] Checkpoint guidance saved to {checkpoint_file}")

        return review_result["guidance"]

    async def _complete_experiment(
        self,
        exp_id: str,
        problem_id: str,
        success: bool,
        iterations: int,
        final_solution: Optional[str],
        mode: str = "iterative",
        benchmark_run_id: Optional[str] = None
    ) -> dict:
        """Complete experiment and store results.

        Args:
            exp_id: Experiment ID
            problem_id: Problem ID
            success: Whether experiment succeeded
            iterations: Total iterations
            final_solution: Final solution code (if successful)
            mode: Evaluation mode (zero-shot or iterative)
            benchmark_run_id: Optional benchmark run ID to group experiments

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

        # Build tags - include benchmark_run_id if provided
        tags = ["result", exp_id, problem_id, "completed"]
        if benchmark_run_id:
            tags.append(benchmark_run_id)

        # Build metadata - include benchmark_run_id if provided
        metadata = {
            "experiment_id": exp_id,
            "problem_id": problem_id,
            "success": success,
            "iterations": iterations,
            **cost_analysis,
            "timestamp": datetime.now().isoformat()
        }
        if benchmark_run_id:
            metadata["benchmark_run_id"] = benchmark_run_id
        if getattr(self, '_no_spec', False):
            metadata["no_spec"] = True
        if getattr(self, '_no_checkpoints', False):
            metadata["no_checkpoints"] = True

        # Store final result
        with self._timed("cortex_remember"):
            await self.cortex.remember(
                title=f"Experiment {exp_id} - COMPLETED",
                content=result_content,
                category="learning",
                tags=tags,
                importance="high",
                metadata=metadata
            )

        # End session (triggers consolidation)
        with self._timed("cortex_end_session"):
            await self.cortex.end_session()

        # Print summary
        mode_desc = "Zero-Shot (no feedback)" if mode == "zero-shot" else "Iterative (with test feedback)"
        print(f"\n{'='*60}")
        print(f"Experiment Complete: {exp_id}")
        print(f"{'='*60}")
        print(f"Problem: {problem_id}")
        print(f"Mode: {mode_desc}")
        print(f"Success: {success} (all tests passed)" if success else f"Success: {success}")
        if mode == "zero-shot":
            print(f"Attempts: {iterations}/1")
        else:
            print(f"Iterations: {iterations}")
        print(self.cost_analyzer.format_analysis(iterations))

        if mode == "iterative":
            print("\nNote: Results use iterative evaluation with test feedback,")
            print("      not standard HumanEval zero-shot pass@k metrics.")

        return {
            "experiment_id": exp_id,
            "problem_id": problem_id,
            "success": success,
            "iterations": iterations,
            "cost_analysis": cost_analysis,
            "final_solution": final_solution
        }
