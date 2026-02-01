"""Test comparing spec generation quality: Sonnet 4.5 vs qwen2.5-coder:32b."""

import json
import os
from pathlib import Path

from koderz.models.factory import ModelFactory
from koderz.benchmarks.humaneval import HumanEval

# Load test problems (first 5 for quick test)
humaneval = HumanEval()
problem_ids = humaneval.list_problems()[:5]
problems = [humaneval.get_problem(pid) for pid in problem_ids]

# Initialize model factory
factory = ModelFactory(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)

# Test model - using qwen2.5-coder:32b (medium-sized open-source model)
TEST_LOCAL_MODEL = "qwen2.5-coder:32b"

# Spec generation prompt (from FrontierClient.generate_spec)
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

# Storage for results
results = {
    "sonnet": [],
    "local": []
}

print("=" * 80)
print("SPEC GENERATION COMPARISON TEST")
print("=" * 80)
print(f"\nTesting on {len(problems)} HumanEval problems")
print(f"Models: claude-sonnet-4-5 vs {TEST_LOCAL_MODEL}\n")

for i, problem in enumerate(problems, 1):
    problem_id = problem["task_id"]
    problem_prompt = problem["prompt"]

    print(f"\n{'-' * 80}")
    print(f"Problem {i}/{len(problems)}: {problem_id}")
    print(f"{'-' * 80}")

    # Generate spec with Sonnet 4.5
    print("\n[1/2] Generating spec with claude-sonnet-4-5...")
    try:
        sonnet_client = factory.get_client("claude-sonnet-4-5")
        sonnet_result = sonnet_client.generate_spec(
            problem_prompt,
            model="claude-sonnet-4-5"
        )
        sonnet_spec = sonnet_result["spec"]
        sonnet_cost = sonnet_result["cost"]

        print(f"  ✓ Generated ({len(sonnet_spec)} chars, cost: ${sonnet_cost:.4f})")

        results["sonnet"].append({
            "problem_id": problem_id,
            "spec": sonnet_spec,
            "cost": sonnet_cost,
            "length": len(sonnet_spec)
        })
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["sonnet"].append({
            "problem_id": problem_id,
            "error": str(e)
        })

    # Generate spec with local model using the SAME prompt
    print(f"\n[2/2] Generating spec with {TEST_LOCAL_MODEL}...")
    try:
        local_client = factory.get_client(TEST_LOCAL_MODEL)

        # Use the same structured prompt that Sonnet gets
        spec_prompt = create_spec_prompt(problem_prompt)
        local_spec = local_client.generate(spec_prompt, model=TEST_LOCAL_MODEL)

        print(f"  ✓ Generated ({len(local_spec)} chars, cost: $0.00)")

        results["local"].append({
            "problem_id": problem_id,
            "spec": local_spec,
            "cost": 0.0,
            "length": len(local_spec)
        })
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["local"].append({
            "problem_id": problem_id,
            "error": str(e)
        })

# Save raw results
output_dir = Path("spec_comparison_results")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "raw_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print("RESULTS SUMMARY")
print(f"{'=' * 80}\n")

# Calculate statistics
sonnet_successes = [r for r in results["sonnet"] if "error" not in r]
local_successes = [r for r in results["local"] if "error" not in r]

print(f"Sonnet 4.5 Success Rate: {len(sonnet_successes)}/{len(problems)} ({len(sonnet_successes)/len(problems)*100:.1f}%)")
print(f"{TEST_LOCAL_MODEL} Success Rate: {len(local_successes)}/{len(problems)} ({len(local_successes)/len(problems)*100:.1f}%)")

if sonnet_successes:
    avg_sonnet_length = sum(r["length"] for r in sonnet_successes) / len(sonnet_successes)
    total_sonnet_cost = sum(r["cost"] for r in sonnet_successes)
    print(f"\nSonnet 4.5 Avg Length: {avg_sonnet_length:.0f} chars")
    print(f"Sonnet 4.5 Total Cost: ${total_sonnet_cost:.4f}")

if local_successes:
    avg_local_length = sum(r["length"] for r in local_successes) / len(local_successes)
    print(f"\n{TEST_LOCAL_MODEL} Avg Length: {avg_local_length:.0f} chars")
    print(f"{TEST_LOCAL_MODEL} Total Cost: $0.00")

# Generate detailed comparison report
print(f"\n{'=' * 80}")
print("DETAILED COMPARISON")
print(f"{'=' * 80}\n")

for i, problem in enumerate(problems):
    problem_id = problem["task_id"]

    print(f"\n{'─' * 80}")
    print(f"Problem: {problem_id}")
    print(f"{'─' * 80}")

    sonnet_result = results["sonnet"][i]
    local_result = results["local"][i]

    if "error" not in sonnet_result:
        print(f"\n[Sonnet 4.5] ({sonnet_result['length']} chars, ${sonnet_result['cost']:.4f})")
        print(sonnet_result["spec"][:500] + "..." if len(sonnet_result["spec"]) > 500 else sonnet_result["spec"])
    else:
        print(f"\n[Sonnet 4.5] ERROR: {sonnet_result['error']}")

    if "error" not in local_result:
        print(f"\n[{TEST_LOCAL_MODEL}] ({local_result['length']} chars, $0.00)")
        print(local_result["spec"][:500] + "..." if len(local_result["spec"]) > 500 else local_result["spec"])
    else:
        print(f"\n[{TEST_LOCAL_MODEL}] ERROR: {local_result['error']}")

print(f"\n{'=' * 80}")
print(f"Full results saved to: {output_dir}/raw_results.json")
print(f"{'=' * 80}\n")

# Create side-by-side comparison file
with open(output_dir / "comparison.md", "w") as f:
    f.write(f"# Spec Generation Comparison: Sonnet 4.5 vs {TEST_LOCAL_MODEL}\n\n")
    f.write(f"**Local Model:** {TEST_LOCAL_MODEL}\n")
    f.write(f"**Problems Tested:** {len(problems)}\n\n")

    f.write("## Summary\n\n")
    f.write(f"- **Sonnet 4.5:** {len(sonnet_successes)}/{len(problems)} success ({len(sonnet_successes)/len(problems)*100:.1f}%)\n")
    f.write(f"- **{TEST_LOCAL_MODEL}:** {len(local_successes)}/{len(problems)} success ({len(local_successes)/len(problems)*100:.1f}%)\n\n")

    if sonnet_successes:
        f.write(f"**Sonnet 4.5 Metrics:**\n")
        f.write(f"- Avg length: {avg_sonnet_length:.0f} chars\n")
        f.write(f"- Total cost: ${total_sonnet_cost:.4f}\n\n")

    if local_successes:
        f.write(f"**{TEST_LOCAL_MODEL} Metrics:**\n")
        f.write(f"- Avg length: {avg_local_length:.0f} chars\n")
        f.write(f"- Total cost: $0.00\n\n")

    f.write("## Detailed Comparisons\n\n")

    for i, problem in enumerate(problems):
        problem_id = problem["task_id"]
        f.write(f"### {problem_id}\n\n")

        sonnet_result = results["sonnet"][i]
        local_result = results["local"][i]

        f.write("#### Sonnet 4.5\n\n")
        if "error" not in sonnet_result:
            f.write(f"**Length:** {sonnet_result['length']} chars | **Cost:** ${sonnet_result['cost']:.4f}\n\n")
            f.write("```\n")
            f.write(sonnet_result["spec"])
            f.write("\n```\n\n")
        else:
            f.write(f"**ERROR:** {sonnet_result['error']}\n\n")

        f.write(f"#### {TEST_LOCAL_MODEL}\n\n")
        if "error" not in local_result:
            f.write(f"**Length:** {local_result['length']} chars | **Cost:** $0.00\n\n")
            f.write("```\n")
            f.write(local_result["spec"])
            f.write("\n```\n\n")
        else:
            f.write(f"**ERROR:** {local_result['error']}\n\n")

        f.write("---\n\n")

print(f"Markdown comparison saved to: {output_dir}/comparison.md\n")
