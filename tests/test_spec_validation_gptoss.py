"""Validation Experiment: Test gpt-oss:20b specs with local model execution.

This experiment:
1. Generates specs for 20 HumanEval problems using gpt-oss:20b
2. Uses those specs to guide local model code generation (qwen2.5-coder:32b)
3. Evaluates success rates and iterations needed
4. Compares against baseline (if available)
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from koderz.models.factory import ModelFactory
from koderz.benchmarks.humaneval import HumanEval, verify_solution

# Configuration
NUM_PROBLEMS = 20
SPEC_MODEL = "gpt-oss:20b"
IMPL_MODEL = "qwen2.5-coder:32b"
MAX_ITERATIONS = 5

# Load problems
humaneval = HumanEval()
problem_ids = humaneval.list_problems()[:NUM_PROBLEMS]
problems = [humaneval.get_problem(pid) for pid in problem_ids]

# Initialize model factory
factory = ModelFactory(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)

# Spec generation prompt (same as previous tests)
def create_spec_prompt(problem_text: str) -> str:
    """Create the spec generation prompt."""
    return f"""Generate a MINIMAL implementation specification for the following coding problem:

{problem_text}

Your spec should include ONLY:
1. Problem analysis - What is the core challenge? What are the constraints?
2. Implementation specification - What should the function do? What should it return?

CRITICAL - Do NOT include:
- Implementation approach or algorithm suggestions
- Edge cases or common pitfalls
- Test criteria or examples
- Reference implementation, pseudocode, or code skeleton
- Specific data structures or algorithms to use

Keep the spec minimal. The goal is to clarify WHAT needs to be done, not HOW to do it.
This spec will guide a coding model that should solve the problem independently."""

print("=" * 80)
print("VALIDATION EXPERIMENT: gpt-oss:20b Spec Quality Test")
print("=" * 80)
print(f"\nExperiment Configuration:")
print(f"  Spec Model: {SPEC_MODEL}")
print(f"  Implementation Model: {IMPL_MODEL}")
print(f"  Problems: {NUM_PROBLEMS} (HumanEval/0 to HumanEval/{NUM_PROBLEMS-1})")
print(f"  Max Iterations: {MAX_ITERATIONS}")
print()

# Storage
output_dir = Path("spec_validation_gptoss_results")
output_dir.mkdir(exist_ok=True)

# Phase 1: Generate specs with gpt-oss:20b
print("=" * 80)
print("PHASE 1: Generating Specs with gpt-oss:20b")
print("=" * 80)
print()

specs = []
spec_generation_times = []

for i, problem in enumerate(problems, 1):
    problem_id = problem["task_id"]
    problem_prompt = problem["prompt"]

    print(f"[{i}/{NUM_PROBLEMS}] {problem_id}")

    try:
        start = datetime.now()
        gptoss_client = factory.get_client(SPEC_MODEL)
        spec_prompt = create_spec_prompt(problem_prompt)
        spec = gptoss_client.generate(spec_prompt, model=SPEC_MODEL)
        elapsed = (datetime.now() - start).total_seconds()

        print(f"  ✓ Generated ({len(spec)} chars, {elapsed:.1f}s)")

        specs.append({
            "problem_id": problem_id,
            "spec": spec,
            "length": len(spec),
            "time": elapsed
        })
        spec_generation_times.append(elapsed)

    except Exception as e:
        print(f"  ✗ Error: {e}")
        specs.append({
            "problem_id": problem_id,
            "error": str(e)
        })

# Save specs
with open(output_dir / "specs.json", "w") as f:
    json.dump(specs, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Phase 1 Complete: {len([s for s in specs if 'error' not in s])}/{NUM_PROBLEMS} specs generated")
if spec_generation_times:
    print(f"Average time: {sum(spec_generation_times)/len(spec_generation_times):.1f}s")
print(f"{'=' * 80}\n")

# Phase 2: Run Koderz experiments with generated specs
print("=" * 80)
print("PHASE 2: Running Code Generation with Local Model")
print("=" * 80)
print()

results = []

for i, (problem, spec_data) in enumerate(zip(problems, specs), 1):
    problem_id = problem["task_id"]

    if "error" in spec_data:
        print(f"[{i}/{NUM_PROBLEMS}] {problem_id} - SKIPPED (no spec)")
        results.append({
            "problem_id": problem_id,
            "status": "skipped",
            "reason": "spec_generation_failed"
        })
        continue

    print(f"[{i}/{NUM_PROBLEMS}] {problem_id}")
    print(f"  Spec: {spec_data['length']} chars")

    # Create implementation prompt combining spec + problem
    impl_prompt = f"""You are implementing a solution based on this specification:

{spec_data['spec']}

Original problem:
{problem['prompt']}

Generate a complete, working Python implementation. Output ONLY the code, no explanations."""

    # Track iterations
    iterations_data = []
    solution = None

    for iteration in range(1, MAX_ITERATIONS + 1):
        try:
            print(f"  Iteration {iteration}/{MAX_ITERATIONS}...", end=" ", flush=True)

            start = datetime.now()
            impl_client = factory.get_client(IMPL_MODEL)
            code = impl_client.generate(impl_prompt, model=IMPL_MODEL)
            elapsed = (datetime.now() - start).total_seconds()

            # Extract code (remove markdown code blocks if present)
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            # Test the solution
            test_result = verify_solution(problem, code)

            iterations_data.append({
                "iteration": iteration,
                "time": elapsed,
                "code_length": len(code),
                "passed": test_result["success"],
                "tests_passed": test_result.get("tests_passed", 0),
                "tests_total": test_result.get("tests_total", 0)
            })

            if test_result["success"]:
                print(f"✓ PASSED ({elapsed:.1f}s)")
                solution = code
                break
            else:
                print(f"✗ Failed ({elapsed:.1f}s)")
                # Update prompt with feedback for next iteration
                impl_prompt += f"\n\nPrevious attempt failed tests. Errors: {test_result.get('error', 'Unknown')}"

        except Exception as e:
            print(f"✗ Error: {e}")
            iterations_data.append({
                "iteration": iteration,
                "error": str(e)
            })
            break

    # Record final result
    success = solution is not None
    results.append({
        "problem_id": problem_id,
        "status": "solved" if success else "failed",
        "iterations": iterations_data,
        "total_iterations": len(iterations_data),
        "solved_at_iteration": next((it["iteration"] for it in iterations_data if it.get("passed")), None),
        "final_code": solution if success else None
    })

    if success:
        print(f"  Result: ✓ SOLVED at iteration {results[-1]['solved_at_iteration']}")
    else:
        print(f"  Result: ✗ FAILED after {len(iterations_data)} iterations")
    print()

# Save results
with open(output_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)

# Phase 3: Analysis
print("=" * 80)
print("PHASE 3: Analysis")
print("=" * 80)
print()

solved = [r for r in results if r["status"] == "solved"]
failed = [r for r in results if r["status"] == "failed"]
skipped = [r for r in results if r["status"] == "skipped"]

print(f"Success Rate: {len(solved)}/{NUM_PROBLEMS} ({len(solved)/NUM_PROBLEMS*100:.1f}%)")
print(f"  Solved: {len(solved)}")
print(f"  Failed: {len(failed)}")
print(f"  Skipped: {len(skipped)}")
print()

if solved:
    avg_iterations = sum(r["solved_at_iteration"] for r in solved) / len(solved)
    print(f"Average Iterations to Solve: {avg_iterations:.2f}")

    iteration_distribution = {}
    for r in solved:
        it = r["solved_at_iteration"]
        iteration_distribution[it] = iteration_distribution.get(it, 0) + 1

    print(f"\nIteration Distribution:")
    for iteration in sorted(iteration_distribution.keys()):
        count = iteration_distribution[iteration]
        print(f"  Iteration {iteration}: {count} problems ({count/len(solved)*100:.1f}%)")

print()

# Failed problems analysis
if failed:
    print(f"Failed Problems ({len(failed)}):")
    for r in failed:
        print(f"  {r['problem_id']} - {r['total_iterations']} iterations attempted")

print()
print("=" * 80)
print(f"Results saved to: {output_dir}/")
print("=" * 80)
print()

# Create summary report
with open(output_dir / "summary.md", "w") as f:
    f.write(f"# gpt-oss:20b Spec Validation Experiment\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Spec Model:** {SPEC_MODEL}\n")
    f.write(f"**Implementation Model:** {IMPL_MODEL}\n")
    f.write(f"**Problems:** {NUM_PROBLEMS}\n")
    f.write(f"**Max Iterations:** {MAX_ITERATIONS}\n\n")

    f.write(f"## Results\n\n")
    f.write(f"**Success Rate:** {len(solved)}/{NUM_PROBLEMS} ({len(solved)/NUM_PROBLEMS*100:.1f}%)\n\n")

    if solved:
        f.write(f"**Average Iterations to Solve:** {avg_iterations:.2f}\n\n")

        f.write(f"### Iteration Distribution\n\n")
        f.write(f"| Iteration | Problems Solved | Percentage |\n")
        f.write(f"|-----------|-----------------|------------|\n")
        for iteration in sorted(iteration_distribution.keys()):
            count = iteration_distribution[iteration]
            f.write(f"| {iteration} | {count} | {count/len(solved)*100:.1f}% |\n")
        f.write(f"\n")

    f.write(f"### Problem-by-Problem Results\n\n")
    f.write(f"| Problem ID | Status | Iterations |\n")
    f.write(f"|------------|--------|------------|\n")
    for r in results:
        status = "✓ Solved" if r["status"] == "solved" else ("✗ Failed" if r["status"] == "failed" else "⊘ Skipped")
        iterations = r.get("solved_at_iteration", r.get("total_iterations", "-"))
        f.write(f"| {r['problem_id']} | {status} | {iterations} |\n")

print(f"Summary report: {output_dir}/summary.md\n")
