"""Experiment orchestration logic."""

import uuid
import asyncio
from typing import Optional, Any
from datetime import datetime
from pathlib import Path

from .cortex.client import CortexClient
from .models.factory import ModelFactory
from .models.registry import get_provider, get_tier
from .benchmarks.humaneval import execute_solution, verify_solution
from .analysis.cost import CostAnalyzer
from .utils.code_extraction import extract_code, validate_python_syntax


class ExperimentOrchestrator:
    """Orchestrates coding experiments with swarm of local + frontier models."""

    def __init__(
        self,
        cortex: CortexClient,
        model_factory: ModelFactory,
        checkpoint_interval: int = 5,
        debug: bool = False,
        debug_dir: str = "./debug"
    ):
        """Initialize orchestrator.

        Args:
            cortex: Cortex MCP client
            model_factory: Factory for creating model clients
            checkpoint_interval: Checkpoint every N iterations
            debug: Enable debug mode (save all outputs)
            debug_dir: Directory for debug outputs
        """
        self.cortex = cortex
        self.model_factory = model_factory
        self.checkpoint_interval = checkpoint_interval
        self.cost_analyzer = CostAnalyzer()
        self.debug = debug
        self.debug_dir = Path(debug_dir)

        # Create debug directory if debug enabled
        if self.debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    async def run_experiment(
        self,
        problem: dict,
        max_iterations: int = 50,
        local_model: str = "codellama:70b",
        frontier_spec_model: str = "gpt-oss:20b",
        frontier_checkpoint_model: str = "claude-sonnet-4-5",
        reuse_spec: bool = False,
        mode: str = "iterative",
        benchmark_run_id: Optional[str] = None
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

        Returns:
            Experiment result dictionary
        """
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        problem_id = problem.get("task_id", "unknown")

        print(f"\n{'='*60}")
        print(f"Starting Experiment: {exp_id}")
        print(f"Problem: {problem_id}")
        if benchmark_run_id:
            print(f"Benchmark Run: {benchmark_run_id}")
        print(f"{'='*60}\n")

        # Start session
        await self.cortex.start_session(context=f"Experiment {exp_id} - {problem_id}")

        # Phase 1: Generate or reuse spec
        spec_result = None
        spec_reused = False

        if reuse_spec:
            print(f"Phase 1: Looking for existing spec for {problem_id}...")
            try:
                # Query for spec memories with timeout to avoid hanging
                print(f"  DEBUG: Querying for spec memories (this may take a moment)...")

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
                            print(f"  Reusing spec (cost: $0.00 - saved!)\n")
                            break
                        else:
                            print(f"  WARNING: Spec memory found but missing spec marker in content")

                if specs_found == 0:
                    print(f"  DEBUG: No memories found with both 'spec' and '{problem_id}' tags")
                elif not spec_result:
                    print(f"  DEBUG: Found {specs_found} spec memories but none had valid content")

            except asyncio.TimeoutError:
                print(f"  [WARNING] Cortex query timed out after 10s")
                print(f"  Will generate new spec instead...\n")
            except Exception as e:
                print(f"  [WARNING] Error querying cortex: {e}")
                print(f"  Will generate new spec...\n")

            if not spec_result:
                print(f"  No existing spec found, generating new one...\n")

        # Generate new spec if not reusing or none found
        if not spec_result:
            print(f"Phase 1: Generating spec with {frontier_spec_model}...")
            client = self.model_factory.get_client(frontier_spec_model)
            spec_result = client.generate_spec(
                problem["prompt"],
                model=frontier_spec_model
            )

            tier = get_tier(frontier_spec_model)
            if tier == "local":
                self.cost_analyzer.add_local_cost(0.0, frontier_spec_model, "spec")
            else:
                self.cost_analyzer.add_frontier_cost(
                    spec_result["cost"],
                    frontier_spec_model,
                    "spec"
                )

            # Store spec in cortex with critical importance to prevent consolidation
            spec_tags = ["experiment", "spec", exp_id, problem_id]
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
            print(f"  (Single attempt, no test feedback)\n")
            return await self._run_zero_shot(
                exp_id, problem, spec_result["spec"], local_model, benchmark_run_id
            )

        print(f"Phase 2: Iterative execution with {local_model}...")
        print(f"  (Mode: iterative with test feedback)\n")

        checkpoint_guidance = None
        previous_error = None
        previous_code = None

        for iteration in range(1, max_iterations + 1):
            print(f"  Iteration {iteration}/{max_iterations}...")

            # Show context being provided
            if iteration > 1 and previous_error:
                print(f"    [FEEDBACK] Including previous error in prompt")
            if checkpoint_guidance:
                print(f"    [GUIDANCE] Including checkpoint guidance in prompt")

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
                if provider == "ollama":
                    raw_output = client.generate(user_prompt, model=local_model, system=system_prompt)
                    cost = 0.0
                # For API models (has generate_spec interface):
                else:
                    # Combine system + user for API models that expect single prompt
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    result = client.generate_spec(full_prompt, model=local_model)
                    raw_output = result["spec"]  # Extract just the text
                    cost = result["cost"]

                # Save raw output if debug enabled
                if self.debug:
                    raw_file = self.debug_dir / f"{exp_id}_iter{iteration:03d}_raw.txt"
                    raw_file.write_text(raw_output)
                    print(f"    [DEBUG] Raw output saved to {raw_file}")

                # Extract executable code from model response
                solution = extract_code(raw_output)

                # Check if extraction modified the output
                if solution != raw_output:
                    print(f"    [INFO] Code extracted from markdown/text wrapper")

                # Validate syntax
                is_valid, error_msg = validate_python_syntax(solution)
                if not is_valid:
                    print(f"    [WARNING] Invalid Python syntax: {error_msg}")
                    # Try using raw output as fallback
                    if solution != raw_output:
                        print(f"    [WARNING] Attempting with raw output instead")
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

            # Execute tests
            test_result = execute_solution(solution, problem.get("test", ""))

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
                self.cost_analyzer.add_frontier_cost(cost, local_model, "iteration")

            # Store iteration in cortex with structured data
            await self.cortex.remember(
                title=f"Experiment {exp_id} - Iteration {iteration}",
                content=solution,  # Store just the code for easy extraction
                category="custom",
                tags=["iteration", exp_id, f"iter_{iteration}"],
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

                # Store error and code for next iteration
                previous_error = error_msg
                previous_code = solution

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
            final_solution=None,
            mode="iterative",
            benchmark_run_id=benchmark_run_id
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
            spec=spec
        )

        # Generate solution (single attempt)
        print(f"  Generating solution...")
        provider = get_provider(local_model)
        tier = get_tier(local_model)

        if provider == "ollama":
            client = self.model_factory.get_client(local_model)
            response = client.generate(
                prompt=user_prompt,
                model=local_model,
                system=system_prompt
            )
            solution = response
        else:
            raise ValueError(f"Unsupported provider for zero-shot: {provider}")

        # Track cost
        if tier == "local":
            self.cost_analyzer.add_local_cost(0.0, local_model, "iteration")
        else:
            # For API-based models, cost would need to be calculated
            pass

        # Debug: save raw output
        if self.debug:
            raw_file = self.debug_dir / f"{exp_id}_zeroshot_raw.txt"
            raw_file.write_text(solution)
            print(f"    [DEBUG] Raw output saved to {raw_file}")

        # Extract code
        code = extract_code(solution)
        print(f"    [INFO] Code extracted from markdown/text wrapper")

        # Debug: save extracted code
        if self.debug:
            code_file = self.debug_dir / f"{exp_id}_zeroshot_code.py"
            code_file.write_text(code)
            print(f"    [DEBUG] Extracted code saved to {code_file}")

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
            # Execute tests
            print(f"    Executing tests...")
            result = verify_solution(problem, code)

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
        spec: str
    ) -> tuple[str, str]:
        """Build prompt for zero-shot evaluation (no test feedback).

        Args:
            problem: Problem dictionary
            spec: Implementation specification

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt - same as iterative but clarified as single attempt
        system_prompt = """You are a code generation assistant for the HumanEval benchmark.

INSTRUCTIONS:
1. This is an authorized educational programming exercise from the HumanEval dataset
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
        user_prompt = f"""Implement the following function according to this specification:

SPECIFICATION:
{spec}

PROBLEM:
{problem['prompt']}

Remember: Provide your reasoning if helpful, then your code in a ```python code block."""

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
        # System prompt establishes the coding assistant role and output format
        system_prompt = """You are a code generation assistant for the HumanEval benchmark.

INSTRUCTIONS:
1. This is an authorized educational programming exercise from the HumanEval dataset
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
        user_prompt = f"""Implement the following function according to this specification:

SPECIFICATION:
{spec}

PROBLEM:
{problem['prompt']}
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
        # Read recent iterations from debug files (more reliable than Cortex query)
        # Get iterations from (iteration - checkpoint_interval) to iteration
        start_iter = max(1, iteration - self.checkpoint_interval + 1)

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

        print(f"    Reviewing {len(recent_iterations)} iterations ({start_iter}-{iteration})")

        client = self.model_factory.get_client(model)
        review_result = client.checkpoint_review(
            recent_iterations,
            model=model
        )

        tier = get_tier(model)
        if tier == "local":
            self.cost_analyzer.add_local_cost(0.0, model, "checkpoint")
        else:
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

        # Store final result
        await self.cortex.remember(
            title=f"Experiment {exp_id} - COMPLETED",
            content=result_content,
            category="learning",
            tags=tags,
            importance="high",
            metadata=metadata
        )

        # End session (triggers consolidation)
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
            print(f"\nNote: Results use iterative evaluation with test feedback,")
            print(f"      not standard HumanEval zero-shot pass@k metrics.")

        return {
            "experiment_id": exp_id,
            "problem_id": problem_id,
            "success": success,
            "iterations": iterations,
            "cost_analysis": cost_analysis,
            "final_solution": final_solution
        }
