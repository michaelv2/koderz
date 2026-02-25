# Iteration Attribution Analysis: Checkpoint Guidance vs. Self-Recovery

**Date**: 2026-02-24
**Dataset**: HumanEval (164 problems), Studies 1-2 from FRONTIER_GUIDANCE_STUDY.md
**Models**: gpt-oss:20b-128k, qwen3-coder:latest, nemotron-3-nano:30b
**Checkpoint models**: claude-sonnet-4-5, gpt-5-nano, gpt-4.1-nano, claude-haiku-4-5

## Research Questions

1. **In aggregate, how often is the frontier checkpoint that steers local models to success vs. the model self-correcting from test feedback alone?**
2. **What can we learn from non-checkpoint successes about model reasoning, and how could this inform better orchestration/prompting/model selection?**

---

## Methodology

### Classification

Each problem outcome is classified based on which iteration solved it and whether checkpoint guidance was available:

| Category | Iterations | Has Checkpoint? | Meaning |
|:---------|:-----------|:----------------|:--------|
| **First pass** | 1 | No | Spec + model capability was sufficient |
| **Self-recovery** | 2-5 | No | Model corrected itself using test error feedback only |
| **Post-checkpoint** | 6+ | Yes (CP fires after iter 5) | Model had frontier checkpoint guidance available |
| **Failed** | max | Both | Problem unsolved |

**Checkpoint timing**: The orchestrator runs the iteration attempt, checks test results, and then fires the checkpoint *after* iteration 5 (and 10, 15). So iteration 5 is the last attempt *without* guidance; iteration 6 is the first attempt *with* guidance. The self-recovery/post-checkpoint boundary is clean.

**Self-recovery information available**: On iterations 2-5, the model receives:
- The original spec
- Its previous code that failed
- The exact error message (assertion errors, type errors, etc.)
- A structured debugging prompt ("trace through step-by-step, identify the failing input...")

**Post-checkpoint additional information**: After iteration 5, the model also receives:
- "CODE REVIEW FEEDBACK FROM EXPERT" — the frontier checkpoint model's analysis of all attempts so far, including failure patterns and strategic guidance

---

## Part 1: Aggregate Attribution

### Core Finding: 82-84% of multi-iteration successes are self-recovery

Across all 12 benchmark runs (3 models × 3 iteration configs + 3 checkpoint model variants):

| Category | Count | % of multi-iter successes |
|:---------|:------|:--------------------------|
| Self-recovery (iter 2-5) | 64 | **84%** |
| Post-checkpoint (iter 6+) | 12 | **16%** |

### Per-Model Breakdown (deduplicated, 10-iteration configs)

| Model (CP model) | First Pass | Self-Recovery | Post-Checkpoint | Failed | SR% of multi-iter |
|:-----------------|:-----------|:--------------|:----------------|:-------|:-------------------|
| gpt-oss:20b-128k (Sonnet) | 149 | 10 | 2 | 3 | **83%** |
| nemotron-3-nano:30b (Sonnet) | 154 | 5 | 1 | 4 | **83%** |
| qwen3-coder:latest (Sonnet) | 152 | 4 | 3 | 5 | **57%** |
| gpt-oss (gpt-5-nano) | 155 | 5 | 1 | 3 | **83%** |
| gpt-oss (gpt-4.1-nano) | 155 | 5 | 0 | 4 | **100%** |
| gpt-oss (Haiku) | 157 | 3 | 0 | 4 | **100%** |

**Interpretation**: gpt-oss and nemotron self-correct ~83% of their multi-iteration problems from test feedback alone. qwen3-coder is more checkpoint-dependent (only 57% self-recovery), needing guidance for problems the other models handle without help.

### Iteration Distribution (all successful problems)

| Iteration | Count | Notes |
|:----------|:------|:------|
| 1 | 1,838 | 96.2% of all successes — spec + first attempt |
| 2 | 53 | Dominant self-recovery iteration |
| 3 | 5 | |
| 4 | 3 | |
| 5 | 3 | Last attempt before checkpoint fires |
| 6 | 3 | First attempt with checkpoint guidance |
| 7 | 4 | |
| 8 | 2 | |
| 9 | 1 | |
| 10 | 1 | |
| 12 | 1 | |

**Key observation**: Iteration 2 accounts for **70% of all multi-iteration successes** (53/76). The pattern is overwhelmingly: fail once, fix from test feedback on the immediate next try. Very few problems require a gradual multi-step correction.

### What the checkpoints actually unlock

Only **7 unique problems** across all models were ever solved post-checkpoint (iter 6+):

| Problem | Models that needed CP | Models that solved it as P1 or SR | Nature of CP value |
|:--------|:----------------------|:----------------------------------|:-------------------|
| HumanEval/76 | gpt-oss (iter 7) | nemotron (P1), qwen3 (P1) | Algorithm direction change |
| HumanEval/103 | gpt-oss (iter 8-12), qwen3 (iter 7) | nemotron (P1) | Python banker's rounding insight |
| HumanEval/113 | qwen3 (iter 7) | gpt-oss (P1), nemotron (P1) | qwen3-specific |
| HumanEval/130 | qwen3 (iter 6-9) | gpt-oss (P1), nemotron (P1) | qwen3-specific |
| HumanEval/145 | gpt-oss (iter 8) | — (all others fail) | Truly hard (only solved once) |
| HumanEval/163 | nemotron (iter 6) | gpt-oss (SR), qwen3 (P1) | nemotron-specific |

**Critical insight**: 4 of 7 checkpoint-dependent problems are model-specific — one model needs the checkpoint, but another model solves it on the first try. Only HumanEval/103 consistently requires checkpoint guidance across multiple models, and even then nemotron solves it at P1.

---

## Part 2: What Self-Recovery Tells Us About Model Reasoning

### 2.1 The "One-Shot Fix" Pattern

The dominant self-recovery pattern is solving at iteration 2 (53/64 self-recoveries = 83%). This means:

- **Attempt 1**: Model generates a plausible solution from the spec
- **Test feedback**: Specific error (assertion failure, type error, edge case)
- **Attempt 2**: Model analyzes the error, identifies the exact fix, succeeds

This pattern is nearly universal across all three models. It suggests the errors are **implementation bugs** (off-by-one, wrong operator, forgotten edge case), not **conceptual misunderstandings**. The model "knows" the right approach but makes a localized mistake.

**Common self-recovery problems and their error patterns**:

| Problem | Nature of iter-1 error | Why iter 2 succeeds |
|:--------|:-----------------------|:--------------------|
| HumanEval/38 (decode_cyclic) | String grouping off-by-one | Test output shows exact wrong character positions |
| HumanEval/50 (decode_shift) | Modular arithmetic direction | Assertion shows shift went wrong way |
| HumanEval/75 (is_multiply_prime) | Product-of-3-primes misinterpreted | Test catches non-prime factor |
| HumanEval/93 (encode) | Missing case-swap step | Output comparison reveals unchanged case |
| HumanEval/97 (multiply) | Negative number unit digit | Assertion with negative input exposes issue |
| HumanEval/127 (intersection) | Interval boundary inclusion | Wrong boolean for a specific interval pair |
| HumanEval/140 (fix_spaces) | Consecutive-space grouping | String comparison shows wrong replacement |

**The test feedback is acting as a "compiler error" for logical mistakes.** The structured debug prompt ("trace through step-by-step with the failing input") is effective because the model already has the right algorithm — it just needs to find the bug.

### 2.2 The "Stuck in a Rut" Pattern (Checkpoint-Dependent Problems)

Post-checkpoint problems are qualitatively different. The model doesn't just have a bug — it's using the **wrong approach entirely**:

**HumanEval/76 (is_simple_power)**: gpt-oss checks divisibility (`x % n == 0`) instead of iterative exponentiation. Test feedback says "Wrong!" but the model keeps trying divisibility variants. The checkpoint says "use repeated multiplication" — a fundamental strategy change.

**HumanEval/103 (rounded_avg)**: Models use floating-point averaging and hit Python's banker's rounding behavior (`round(14.5) = 14`). Each iteration tries another float-manipulation trick. The checkpoint identifies the rounding semantics issue explicitly.

**HumanEval/113, /130 (qwen3-only)**: qwen3-coder gets stuck in loops where successive attempts oscillate between two wrong approaches. The checkpoint breaks the oscillation by identifying what both approaches have in common and suggesting a third path.

**Pattern**: The frontier checkpoint is valuable when the model is in a **local minimum** — repeatedly trying variations of a fundamentally wrong approach. Test feedback alone can't escape this because the feedback says *what* is wrong but not *which direction to go*.

### 2.3 The Model-Specificity of Difficulty

The cross-model comparison reveals that "checkpoint-dependent" is often a property of the **model**, not the **problem**:

```
HumanEval/103:  gpt-oss CP(10)  |  qwen3 CP(7)  |  nemotron P1
HumanEval/76:   gpt-oss CP(7)   |  qwen3 P1     |  nemotron P1
HumanEval/113:  gpt-oss P1      |  qwen3 CP(7)  |  nemotron P1
HumanEval/130:  gpt-oss P1      |  qwen3 CP(6)  |  nemotron P1
HumanEval/163:  gpt-oss SR(2)   |  qwen3 P1     |  nemotron CP(6)
```

**No problem requires checkpoints for all 3 models.** Every checkpoint-dependent problem for one model is either P1 or SR for at least one other model. This means:
- The problems aren't inherently hard — they expose **model-specific blind spots**
- A different model would have solved it without the checkpoint expense
- This validates the ensemble approach over the checkpoint approach for marginal problems

### 2.4 qwen3-coder's Checkpoint Dependency

qwen3-coder is an outlier: only 57% self-recovery vs. 83% for the other two models. Its checkpoint-dependent problems (HumanEval/103, /113, /130) are all solved at P1 by the other models. Additionally, qwen3 shows:
- **More regressions**: 5 problems that passed in zero-shot fail with spec+iterations at 5 iter
- **Non-determinism**: HumanEval/99 passes at 5-iter, fails at 10-iter, passes at 15-iter
- **Longer recovery times**: Its self-recovery problems average iter 2.5 vs. iter 2.1 for gpt-oss

This suggests qwen3-coder is **more sensitive to prompt perturbation** and **less effective at self-debugging**. The spec sometimes confuses it, and it's less systematic about using test feedback to localize bugs.

---

## Part 3: Implications for Orchestration

### 3.1 Checkpoint Interval Optimization

With 84% of multi-iteration successes happening in iterations 2-5 (before any checkpoint), the current checkpoint interval of 5 is reasonable but the checkpoints themselves are often wasted:

- **160/164 problems** never reach a checkpoint (solved at P1 or SR)
- **Only 3-4 problems per model** ever benefit from checkpoint guidance
- Cost of unused checkpoints: for the typical run, checkpoints are called on ~4 problems that fail after 5 iterations, but only 1-2 of those actually benefit

**Recommendation**: Consider a "checkpoint on demand" strategy — only fire checkpoints when the model shows signs of being stuck (e.g., repeated similar errors across 3+ iterations, or oscillating between two solutions). This would cut checkpoint costs by ~50% while preserving value.

### 3.2 Early Exit Optimization

The iteration distribution suggests most value is captured by iteration 3:
- Iteration 1: 96.2% of problems solved
- Iteration 2: +2.8% (cumulative 99.0%)
- Iteration 3: +0.3% (cumulative 99.3%)
- Iterations 4-5: +0.3% more (cumulative 99.6%)

For cost-sensitive deployments, a max_iterations=3 policy with selective checkpoint escalation on failures would capture 99.3% of solvable problems at minimal iteration cost.

### 3.3 Model Selection Strategy

The model-specificity finding suggests a **cascade strategy** rather than a fixed model:

1. **Try the cheapest/fastest model first** (gpt-oss:20b-128k, highest P1 rate)
2. **On failure after 2-3 iterations**, switch to a different model rather than continuing
3. **Reserve checkpoints** for problems where 2+ models have failed

This is essentially the ensemble approach from Study 3, but applied dynamically rather than requiring full parallel runs.

### 3.4 Test Feedback Enhancement

Since self-recovery is the dominant success mechanism (84%), improving test feedback quality would have more impact than improving checkpoint quality:

- **Include the specific failing input** (currently just the assertion error message)
- **Show expected vs. actual output** explicitly for assertion failures
- **Highlight which test case failed** (first, middle, edge case)
- **For partial pass rates**: show how many tests passed and which category failed

The current debug prompt ("trace through step-by-step") is effective — the iteration-2 dominance proves it. But making the test output more structured could shift some iteration-3+ cases to iteration-2 successes.

### 3.5 Spec Quality as the Hidden Variable

The analysis reveals that **spec generation is the highest-leverage intervention**:
- 149-157 out of 164 problems (91-96%) are solved on the first iteration with a spec
- HumanEval/91 (unsolvable in zero-shot by all models) becomes trivially solvable with spec
- qwen3-coder regressions are caused by the spec confusing the model on certain problems

Improving spec quality or making specs model-aware (different spec styles for different models) could reduce multi-iteration problems further. The spec is currently generated once and shared; a spec that anticipates common model blind spots could prevent first-attempt failures.

### 3.6 Implications for Benchmarking

**For evaluating model coding ability**:
- Zero-shot benchmarks undercount model capability by 3-5% (the gap between ZS and iterative scores)
- A "2-attempt" benchmark (one retry with test feedback) would capture 97-99% of true model capability
- Checkpoint benchmarks mostly measure whether a different model would have gotten the answer, not whether guidance helps

**For cost-optimized production pipelines**:
- The optimal strategy is: spec + 2 attempts + model fallback, not: spec + 10 attempts + checkpoints
- Checkpoint guidance has a narrow value band: ~1-3 problems per 164 (~1%) where it uniquely helps
- Ensemble/cascade approaches are more cost-effective than checkpoint approaches for marginal problems

---

## Summary

| Finding | Data |
|:--------|:-----|
| Self-recovery rate (all models) | **84%** of multi-iteration successes |
| Dominant recovery iteration | **Iteration 2** (70% of multi-iter successes) |
| Problems ever requiring checkpoints | **7 unique** out of 164 |
| Checkpoint-specific value (not solvable by another model at P1) | **1-2 problems** (HumanEval/103, maybe /145) |
| qwen3-coder self-recovery rate | **57%** (vs. 83% for gpt-oss and nemotron) |
| First-pass solve rate (with spec) | **91-96%** depending on model |
| Problems needing >2 iterations | **<1%** of all problems |

**The bottom line**: Test feedback from failed runs is the primary driver of iterative improvement, not frontier checkpoint guidance. Frontier checkpoints have narrow but real value for a small number of "stuck" problems where the model is pursuing fundamentally wrong strategies. For most problems, a retry with error context is all that's needed.

---

## Data Sources

| Source | File |
|:-------|:-----|
| Study 1 (9 runs) | `benchmark_results/bench_{e1cd2ab5,faa1e88d,4a439714,23d9e9df,b4111968,9b5bfc3e,b2e16b77,76a06d1e,c9da5402}_*.json` |
| Study 2 (3 runs) | `benchmark_results/bench_{9d5ae700,212c9aca,57a64320}_*.json` |
| Analysis script | `analyze_iteration_attribution.py` |
| Study overview | `docs/FRONTIER_GUIDANCE_STUDY.md` |
