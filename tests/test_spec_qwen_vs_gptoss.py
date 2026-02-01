"""Compare spec generation: qwen2.5-coder:32b vs gpt-oss:20b (reusing qwen results)."""

import json
import os
from pathlib import Path
from datetime import datetime

from koderz.models.factory import ModelFactory
from koderz.benchmarks.humaneval import HumanEval

# Load test problems (same 5 as before)
humaneval = HumanEval()
problem_ids = humaneval.list_problems()[:5]
problems = [humaneval.get_problem(pid) for pid in problem_ids]

# Initialize model factory
factory = ModelFactory(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)

# Spec generation prompt
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

# Load qwen results from previous run
print("=" * 80)
print("LOADING QWEN RESULTS FROM PREVIOUS RUN")
print("=" * 80)

qwen_results_file = Path("spec_comparison_3way_results/raw_results.json")
with open(qwen_results_file) as f:
    previous_results = json.load(f)
    qwen_results = previous_results["qwen"]
    sonnet_results = previous_results["sonnet"]  # Also grab Sonnet for reference

print(f"✓ Loaded {len(qwen_results)} qwen results from previous run")
print(f"✓ Loaded {len(sonnet_results)} Sonnet results for reference\n")

# Storage for new results
gptoss_results = []
timing = []

print("=" * 80)
print("GENERATING SPECS WITH gpt-oss:20b")
print("=" * 80)
print(f"\nTesting on {len(problems)} HumanEval problems")
print(f"Models:")
print(f"  1. qwen2.5-coder:32b (32B coding-specialized) - REUSED FROM PREVIOUS RUN")
print(f"  2. gpt-oss:20b (20B general-purpose) - NEW\n")

for i, problem in enumerate(problems, 1):
    problem_id = problem["task_id"]
    problem_prompt = problem["prompt"]

    print(f"\n{'-' * 80}")
    print(f"Problem {i}/{len(problems)}: {problem_id}")
    print(f"{'-' * 80}")

    # Show qwen result (reused)
    qwen_result = qwen_results[i-1]
    if "error" not in qwen_result:
        print(f"\n[qwen2.5-coder:32b - REUSED] ({qwen_result['length']} chars, ${qwen_result['cost']:.2f}, {qwen_result['time']:.1f}s)")
    else:
        print(f"\n[qwen2.5-coder:32b - REUSED] ERROR: {qwen_result['error']}")

    # Generate spec with gpt-oss:20b
    print(f"\n[gpt-oss:20b - NEW] Generating spec...")
    try:
        start = datetime.now()
        gptoss_client = factory.get_client("gpt-oss:20b")
        spec_prompt = create_spec_prompt(problem_prompt)
        gptoss_spec = gptoss_client.generate(spec_prompt, model="gpt-oss:20b")
        elapsed = (datetime.now() - start).total_seconds()

        print(f"  ✓ Generated ({len(gptoss_spec)} chars, cost: $0.00, time: {elapsed:.1f}s)")

        gptoss_results.append({
            "problem_id": problem_id,
            "spec": gptoss_spec,
            "cost": 0.0,
            "length": len(gptoss_spec),
            "time": elapsed
        })
        timing.append(elapsed)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        gptoss_results.append({
            "problem_id": problem_id,
            "error": str(e)
        })

# Save results
output_dir = Path("spec_qwen_vs_gptoss_results")
output_dir.mkdir(exist_ok=True)

results = {
    "sonnet": sonnet_results,  # Include for reference
    "qwen": qwen_results,
    "gptoss": gptoss_results
}

with open(output_dir / "raw_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print("RESULTS SUMMARY")
print(f"{'=' * 80}\n")

# Calculate statistics
qwen_successes = [r for r in qwen_results if "error" not in r]
gptoss_successes = [r for r in gptoss_results if "error" not in r]
sonnet_successes = [r for r in sonnet_results if "error" not in r]

print(f"Sonnet 4.5 (reference baseline):")
if sonnet_successes:
    print(f"  Success Rate: {len(sonnet_successes)}/{len(problems)} ({len(sonnet_successes)/len(problems)*100:.1f}%)")
    avg_length = sum(r["length"] for r in sonnet_successes) / len(sonnet_successes)
    total_cost = sum(r["cost"] for r in sonnet_successes)
    avg_time = sum(r["time"] for r in sonnet_successes) / len(sonnet_successes)
    print(f"  Avg Length: {avg_length:.0f} chars")
    print(f"  Total Cost: ${total_cost:.4f}")
    print(f"  Avg Time: {avg_time:.1f}s")

print(f"\nqwen2.5-coder:32b:")
if qwen_successes:
    print(f"  Success Rate: {len(qwen_successes)}/{len(problems)} ({len(qwen_successes)/len(problems)*100:.1f}%)")
    avg_qwen_length = sum(r["length"] for r in qwen_successes) / len(qwen_successes)
    avg_qwen_time = sum(r["time"] for r in qwen_successes) / len(qwen_successes)
    print(f"  Avg Length: {avg_qwen_length:.0f} chars")
    print(f"  Total Cost: $0.0000")
    print(f"  Avg Time: {avg_qwen_time:.1f}s")

print(f"\ngpt-oss:20b:")
if gptoss_successes:
    print(f"  Success Rate: {len(gptoss_successes)}/{len(problems)} ({len(gptoss_successes)/len(problems)*100:.1f}%)")
    avg_gptoss_length = sum(r["length"] for r in gptoss_successes) / len(gptoss_successes)
    avg_gptoss_time = sum(r["time"] for r in gptoss_successes) / len(gptoss_successes)
    print(f"  Avg Length: {avg_gptoss_length:.0f} chars")
    print(f"  Total Cost: $0.0000")
    print(f"  Avg Time: {avg_gptoss_time:.1f}s")

# Comparative analysis
if qwen_successes and gptoss_successes and sonnet_successes:
    sonnet_avg_len = sum(r["length"] for r in sonnet_successes) / len(sonnet_successes)

    print(f"\n{'=' * 80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'=' * 80}\n")

    print(f"Length Comparison (relative to Sonnet 4.5):")
    print(f"  Sonnet 4.5:        {sonnet_avg_len:.0f} chars (100% baseline)")
    print(f"  qwen2.5-coder:32b: {avg_qwen_length:.0f} chars ({avg_qwen_length/sonnet_avg_len*100:.0f}%)")
    print(f"  gpt-oss:20b:       {avg_gptoss_length:.0f} chars ({avg_gptoss_length/sonnet_avg_len*100:.0f}%)")

    print(f"\nLength Comparison (qwen vs gpt-oss):")
    ratio = avg_qwen_length / avg_gptoss_length
    if ratio > 1:
        print(f"  qwen is {ratio:.1f}x LONGER than gpt-oss ({avg_qwen_length:.0f} vs {avg_gptoss_length:.0f} chars)")
    else:
        print(f"  gpt-oss is {1/ratio:.1f}x LONGER than qwen ({avg_gptoss_length:.0f} vs {avg_qwen_length:.0f} chars)")

    print(f"\nSpeed Comparison:")
    sonnet_avg_time = sum(r["time"] for r in sonnet_successes) / len(sonnet_successes)
    print(f"  Sonnet 4.5:        {sonnet_avg_time:.1f}s (baseline)")
    print(f"  qwen2.5-coder:32b: {avg_qwen_time:.1f}s ({avg_qwen_time/sonnet_avg_time:.1f}x)")
    print(f"  gpt-oss:20b:       {avg_gptoss_time:.1f}s ({avg_gptoss_time/sonnet_avg_time:.1f}x)")

    print(f"\nSpeed Comparison (qwen vs gpt-oss):")
    speed_ratio = avg_qwen_time / avg_gptoss_time
    if speed_ratio > 1:
        print(f"  gpt-oss is {speed_ratio:.1f}x FASTER than qwen ({avg_gptoss_time:.1f}s vs {avg_qwen_time:.1f}s)")
    else:
        print(f"  qwen is {1/speed_ratio:.1f}x FASTER than gpt-oss ({avg_qwen_time:.1f}s vs {avg_gptoss_time:.1f}s)")

# Show first problem in detail
print(f"\n{'=' * 80}")
print("DETAILED COMPARISON (First Problem)")
print(f"{'=' * 80}\n")

if len(problems) > 0:
    problem_id = problems[0]["task_id"]
    print(f"Problem: {problem_id}\n")

    # Sonnet (reference)
    sonnet_result = sonnet_results[0]
    if "error" not in sonnet_result:
        print(f"\n[Sonnet 4.5 - REFERENCE] ({sonnet_result['length']} chars, ${sonnet_result['cost']:.4f}, {sonnet_result['time']:.1f}s)")
        preview = sonnet_result["spec"][:400] + "..." if len(sonnet_result["spec"]) > 400 else sonnet_result["spec"]
        print(preview)

    # Qwen
    qwen_result = qwen_results[0]
    if "error" not in qwen_result:
        print(f"\n[qwen2.5-coder:32b] ({qwen_result['length']} chars, ${qwen_result['cost']:.2f}, {qwen_result['time']:.1f}s)")
        preview = qwen_result["spec"][:400] + "..." if len(qwen_result["spec"]) > 400 else qwen_result["spec"]
        print(preview)

    # GPT-OSS
    gptoss_result = gptoss_results[0]
    if "error" not in gptoss_result:
        print(f"\n[gpt-oss:20b] ({gptoss_result['length']} chars, ${gptoss_result['cost']:.2f}, {gptoss_result['time']:.1f}s)")
        preview = gptoss_result["spec"][:400] + "..." if len(gptoss_result["spec"]) > 400 else gptoss_result["spec"]
        print(preview)
    else:
        print(f"\n[gpt-oss:20b] ERROR: {gptoss_result['error']}")

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_dir}/raw_results.json")
print(f"{'=' * 80}\n")

# Create markdown comparison
with open(output_dir / "comparison.md", "w") as f:
    f.write("# Spec Generation Comparison: qwen2.5-coder:32b vs gpt-oss:20b\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Problems Tested:** {len(problems)}\n\n")

    f.write("## Models\n\n")
    f.write("1. **Sonnet 4.5** - Frontier baseline (reused from previous run)\n")
    f.write("2. **qwen2.5-coder:32b** - 32B parameter coding-specialized model (reused from previous run)\n")
    f.write("3. **gpt-oss:20b** - 20B parameter general-purpose model (newly tested)\n\n")

    f.write("## Summary Statistics\n\n")
    f.write("| Model | Success Rate | Avg Length | Total Cost | Avg Time |\n")
    f.write("|-------|-------------|------------|------------|----------|\n")

    models = [
        ("Sonnet 4.5", sonnet_successes),
        ("qwen2.5-coder:32b", qwen_successes),
        ("gpt-oss:20b", gptoss_successes)
    ]

    for model_name, successes in models:
        if successes:
            avg_length = sum(r["length"] for r in successes) / len(successes)
            total_cost = sum(r["cost"] for r in successes)
            avg_time = sum(r["time"] for r in successes) / len(successes)
            f.write(f"| {model_name} | {len(successes)}/{len(problems)} ({len(successes)/len(problems)*100:.0f}%) | {avg_length:.0f} chars | ${total_cost:.4f} | {avg_time:.1f}s |\n")

    f.write("\n## Detailed Comparisons\n\n")

    for i, problem in enumerate(problems):
        problem_id = problem["task_id"]
        f.write(f"### {problem_id}\n\n")

        # Sonnet
        sonnet_result = sonnet_results[i]
        f.write(f"#### Sonnet 4.5 (Reference)\n\n")
        if "error" not in sonnet_result:
            f.write(f"**Length:** {sonnet_result['length']} chars | **Cost:** ${sonnet_result['cost']:.4f} | **Time:** {sonnet_result['time']:.1f}s\n\n")
            f.write("```\n")
            f.write(sonnet_result["spec"][:500] + "..." if len(sonnet_result["spec"]) > 500 else sonnet_result["spec"])
            f.write("\n```\n\n")

        # Qwen
        qwen_result = qwen_results[i]
        f.write(f"#### qwen2.5-coder:32b\n\n")
        if "error" not in qwen_result:
            f.write(f"**Length:** {qwen_result['length']} chars | **Cost:** ${qwen_result['cost']:.2f} | **Time:** {qwen_result['time']:.1f}s\n\n")
            f.write("```\n")
            f.write(qwen_result["spec"])
            f.write("\n```\n\n")

        # GPT-OSS
        gptoss_result = gptoss_results[i]
        f.write(f"#### gpt-oss:20b\n\n")
        if "error" not in gptoss_result:
            f.write(f"**Length:** {gptoss_result['length']} chars | **Cost:** ${gptoss_result['cost']:.2f} | **Time:** {gptoss_result['time']:.1f}s\n\n")
            f.write("```\n")
            f.write(gptoss_result["spec"])
            f.write("\n```\n\n")
        else:
            f.write(f"**ERROR:** {gptoss_result['error']}\n\n")

        f.write("---\n\n")

print(f"Markdown comparison saved to: {output_dir}/comparison.md\n")
