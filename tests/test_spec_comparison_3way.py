"""Test comparing spec generation quality: Sonnet 4.5 vs llama3.3:70b vs qwen2.5-coder:32b."""

import json
import os
from pathlib import Path
from datetime import datetime

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

# Models to test
MODELS = {
    "sonnet": "claude-sonnet-4-5",
    "llama": "llama3.3:70b",
    "qwen": "qwen2.5-coder:32b"
}

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
    "llama": [],
    "qwen": []
}

# Track timing
timing = {
    "sonnet": [],
    "llama": [],
    "qwen": []
}

print("=" * 80)
print("3-WAY SPEC GENERATION COMPARISON TEST")
print("=" * 80)
print(f"\nTesting on {len(problems)} HumanEval problems")
print(f"Models:")
print(f"  1. claude-sonnet-4-5 (Frontier)")
print(f"  2. llama3.3:70b (70B general-purpose)")
print(f"  3. qwen2.5-coder:32b (32B coding-specialized)\n")

for i, problem in enumerate(problems, 1):
    problem_id = problem["task_id"]
    problem_prompt = problem["prompt"]

    print(f"\n{'-' * 80}")
    print(f"Problem {i}/{len(problems)}: {problem_id}")
    print(f"{'-' * 80}")

    # Generate spec with Sonnet 4.5
    print("\n[1/3] Generating spec with claude-sonnet-4-5...")
    try:
        start = datetime.now()
        sonnet_client = factory.get_client("claude-sonnet-4-5")
        sonnet_result = sonnet_client.generate_spec(
            problem_prompt,
            model="claude-sonnet-4-5"
        )
        elapsed = (datetime.now() - start).total_seconds()

        sonnet_spec = sonnet_result["spec"]
        sonnet_cost = sonnet_result["cost"]

        print(f"  ✓ Generated ({len(sonnet_spec)} chars, cost: ${sonnet_cost:.4f}, time: {elapsed:.1f}s)")

        results["sonnet"].append({
            "problem_id": problem_id,
            "spec": sonnet_spec,
            "cost": sonnet_cost,
            "length": len(sonnet_spec),
            "time": elapsed
        })
        timing["sonnet"].append(elapsed)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["sonnet"].append({
            "problem_id": problem_id,
            "error": str(e)
        })

    # Generate spec with llama3.3:70b
    print(f"\n[2/3] Generating spec with llama3.3:70b...")
    try:
        start = datetime.now()
        llama_client = factory.get_client("llama3.3:70b")
        spec_prompt = create_spec_prompt(problem_prompt)
        llama_spec = llama_client.generate(spec_prompt, model="llama3.3:70b")
        elapsed = (datetime.now() - start).total_seconds()

        print(f"  ✓ Generated ({len(llama_spec)} chars, cost: $0.00, time: {elapsed:.1f}s)")

        results["llama"].append({
            "problem_id": problem_id,
            "spec": llama_spec,
            "cost": 0.0,
            "length": len(llama_spec),
            "time": elapsed
        })
        timing["llama"].append(elapsed)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["llama"].append({
            "problem_id": problem_id,
            "error": str(e)
        })

    # Generate spec with qwen2.5-coder:32b
    print(f"\n[3/3] Generating spec with qwen2.5-coder:32b...")
    try:
        start = datetime.now()
        qwen_client = factory.get_client("qwen2.5-coder:32b")
        spec_prompt = create_spec_prompt(problem_prompt)
        qwen_spec = qwen_client.generate(spec_prompt, model="qwen2.5-coder:32b")
        elapsed = (datetime.now() - start).total_seconds()

        print(f"  ✓ Generated ({len(qwen_spec)} chars, cost: $0.00, time: {elapsed:.1f}s)")

        results["qwen"].append({
            "problem_id": problem_id,
            "spec": qwen_spec,
            "cost": 0.0,
            "length": len(qwen_spec),
            "time": elapsed
        })
        timing["qwen"].append(elapsed)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["qwen"].append({
            "problem_id": problem_id,
            "error": str(e)
        })

# Save raw results
output_dir = Path("spec_comparison_3way_results")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "raw_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print("RESULTS SUMMARY")
print(f"{'=' * 80}\n")

# Calculate statistics for each model
for model_name, model_key in [("Sonnet 4.5", "sonnet"), ("llama3.3:70b", "llama"), ("qwen2.5-coder:32b", "qwen")]:
    successes = [r for r in results[model_key] if "error" not in r]

    print(f"\n{model_name}:")
    print(f"  Success Rate: {len(successes)}/{len(problems)} ({len(successes)/len(problems)*100:.1f}%)")

    if successes:
        avg_length = sum(r["length"] for r in successes) / len(successes)
        total_cost = sum(r["cost"] for r in successes)
        avg_time = sum(r["time"] for r in successes) / len(successes)

        print(f"  Avg Length: {avg_length:.0f} chars")
        print(f"  Total Cost: ${total_cost:.4f}")
        print(f"  Avg Time: {avg_time:.1f}s")

# Comparative analysis
print(f"\n{'=' * 80}")
print("COMPARATIVE ANALYSIS")
print(f"{'=' * 80}\n")

sonnet_successes = [r for r in results["sonnet"] if "error" not in r]
llama_successes = [r for r in results["llama"] if "error" not in r]
qwen_successes = [r for r in results["qwen"] if "error" not in r]

if sonnet_successes and llama_successes and qwen_successes:
    sonnet_avg_len = sum(r["length"] for r in sonnet_successes) / len(sonnet_successes)
    llama_avg_len = sum(r["length"] for r in llama_successes) / len(llama_successes)
    qwen_avg_len = sum(r["length"] for r in qwen_successes) / len(qwen_successes)

    print(f"Length Comparison (relative to Sonnet 4.5):")
    print(f"  Sonnet 4.5:        {sonnet_avg_len:.0f} chars (100%)")
    print(f"  llama3.3:70b:      {llama_avg_len:.0f} chars ({llama_avg_len/sonnet_avg_len*100:.0f}%)")
    print(f"  qwen2.5-coder:32b: {qwen_avg_len:.0f} chars ({qwen_avg_len/sonnet_avg_len*100:.0f}%)")

    sonnet_avg_time = sum(r["time"] for r in sonnet_successes) / len(sonnet_successes)
    llama_avg_time = sum(r["time"] for r in llama_successes) / len(llama_successes)
    qwen_avg_time = sum(r["time"] for r in qwen_successes) / len(qwen_successes)

    print(f"\nSpeed Comparison:")
    print(f"  Sonnet 4.5:        {sonnet_avg_time:.1f}s")
    print(f"  llama3.3:70b:      {llama_avg_time:.1f}s ({llama_avg_time/sonnet_avg_time:.1f}x)")
    print(f"  qwen2.5-coder:32b: {qwen_avg_time:.1f}s ({qwen_avg_time/sonnet_avg_time:.1f}x)")

# Generate detailed comparison report
print(f"\n{'=' * 80}")
print("DETAILED COMPARISON (First Problem)")
print(f"{'=' * 80}\n")

# Show first problem in detail
if len(problems) > 0:
    problem_id = problems[0]["task_id"]
    print(f"Problem: {problem_id}\n")

    for model_name, model_key in [("Sonnet 4.5", "sonnet"), ("llama3.3:70b", "llama"), ("qwen2.5-coder:32b", "qwen")]:
        result = results[model_key][0]

        if "error" not in result:
            print(f"\n[{model_name}] ({result['length']} chars, ${result['cost']:.4f}, {result['time']:.1f}s)")
            preview = result["spec"][:600] + "..." if len(result["spec"]) > 600 else result["spec"]
            print(preview)
        else:
            print(f"\n[{model_name}] ERROR: {result['error']}")

print(f"\n{'=' * 80}")
print(f"Full results saved to: {output_dir}/raw_results.json")
print(f"{'=' * 80}\n")

# Create markdown comparison file
with open(output_dir / "comparison.md", "w") as f:
    f.write("# 3-Way Spec Generation Comparison\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Problems Tested:** {len(problems)}\n\n")

    f.write("## Models\n\n")
    f.write("1. **claude-sonnet-4-5** - Frontier model from Anthropic\n")
    f.write("2. **llama3.3:70b** - 70B parameter general-purpose model from Meta\n")
    f.write("3. **qwen2.5-coder:32b** - 32B parameter coding-specialized model from Alibaba\n\n")

    f.write("## Summary Statistics\n\n")
    f.write("| Model | Success Rate | Avg Length | Total Cost | Avg Time |\n")
    f.write("|-------|-------------|------------|------------|----------|\n")

    for model_name, model_key in [("Sonnet 4.5", "sonnet"), ("llama3.3:70b", "llama"), ("qwen2.5-coder:32b", "qwen")]:
        successes = [r for r in results[model_key] if "error" not in r]
        if successes:
            avg_length = sum(r["length"] for r in successes) / len(successes)
            total_cost = sum(r["cost"] for r in successes)
            avg_time = sum(r["time"] for r in successes) / len(successes)
            f.write(f"| {model_name} | {len(successes)}/{len(problems)} ({len(successes)/len(problems)*100:.0f}%) | {avg_length:.0f} chars | ${total_cost:.4f} | {avg_time:.1f}s |\n")

    f.write("\n## Detailed Comparisons\n\n")

    for i, problem in enumerate(problems):
        problem_id = problem["task_id"]
        f.write(f"### {problem_id}\n\n")

        for model_name, model_key in [("Sonnet 4.5", "sonnet"), ("llama3.3:70b", "llama"), ("qwen2.5-coder:32b", "qwen")]:
            result = results[model_key][i]

            f.write(f"#### {model_name}\n\n")
            if "error" not in result:
                f.write(f"**Length:** {result['length']} chars | **Cost:** ${result['cost']:.4f} | **Time:** {result['time']:.1f}s\n\n")
                f.write("```\n")
                f.write(result["spec"])
                f.write("\n```\n\n")
            else:
                f.write(f"**ERROR:** {result['error']}\n\n")

        f.write("---\n\n")

print(f"Markdown comparison saved to: {output_dir}/comparison.md\n")
