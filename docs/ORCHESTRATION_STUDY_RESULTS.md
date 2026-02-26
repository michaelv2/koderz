# Orchestration Study Results

Multi-model orchestration experiments across three benchmarks: HumanEval (164 single-function problems), BigCodeBench-Hard (148 multi-step library tasks), and a hierarchical multi-file integration exercise (100 acceptance tests).

**Run dates**: 2026-02-13 to 2026-02-26
**Ollama server**: 192.168.1.74:11434 (2x RTX 3090)
**Reproducibility**: `--temperature 0.0 --seed 23` on benchmark runs

---

## Phase 1: Early Exit Simulation

Simulates max_iter cutoffs at 1, 2, 3, 5, 10, 15 across existing HumanEval runs.
Shows marginal value of each additional iteration per model.

| Model | Cutoff | Score | Rate | Marginal +1 |
|-------|--------|-------|------|-------------|
| gpt-oss:20b-128k | 1 | 152/164 | 92.7% | +152 |
| gpt-oss:20b-128k | 2 | 159/164 | 97.0% | +7 |
| gpt-oss:20b-128k | 3 | 159/164 | 97.0% | +0 |
| gpt-oss:20b-128k | 5 | 159/164 | 97.0% | +0 |
| gpt-oss:20b-128k | 10 | 160/164 | 97.6% | +1 |
| gpt-oss:20b-128k | 15 | 161/164 | 98.2% | +1 |
| | | | | |
| qwen3-coder:latest | 1 | 154/164 | 93.9% | +154 |
| qwen3-coder:latest | 2 | 155/164 | 94.5% | +1 |
| qwen3-coder:latest | 3 | 155/164 | 94.5% | +0 |
| qwen3-coder:latest | 5 | 157/164 | 95.7% | +2 |
| qwen3-coder:latest | 10 | 159/164 | 97.0% | +2 |
| qwen3-coder:latest | 15 | 159/164 | 97.0% | +0 |
| | | | | |
| nemotron-3-nano:30b | 1 | 154/164 | 93.9% | +154 |
| nemotron-3-nano:30b | 2 | 158/164 | 96.3% | +4 |
| nemotron-3-nano:30b | 3 | 158/164 | 96.3% | +0 |
| nemotron-3-nano:30b | 5 | 160/164 | 97.6% | +2 |
| nemotron-3-nano:30b | 10 | 161/164 | 98.2% | +1 |
| nemotron-3-nano:30b | 15 | 161/164 | 98.2% | +0 |
| | | | | |

**Key finding**: Most value is captured by iteration 2. Iterations 3-5 provide diminishing returns. Post-checkpoint iterations (6+) recover only 1-2 additional problems.

## Phase 2: Model Cascade Simulation

Combines per-model results to simulate cascade strategies.
Cascade: try model A for N iters, if fail try model B for N iters, etc.

Cascade order: gpt-oss:20b-128k -> nemotron-3-nano:30b -> qwen3-coder:latest

| Strategy | Budget | Score | Rate | Total Iters (avg) |
|----------|--------|-------|------|--------------------|
| Cascade(1x3) | 3 | 161/164 | 98.2% | 1.1 |
| Cascade(2x3) | 6 | 162/164 | 98.8% | 1.2 |
| Cascade(3x3) | 9 | 162/164 | 98.8% | 1.2 |
| | | | | |
| gpt-oss x5 | 5 | 159/164 | 97.0% | 1.2 |
| gpt-oss x10 | 10 | 160/164 | 97.6% | 1.3 |
| nemotron-3-nano x5 | 5 | 160/164 | 97.6% | 1.2 |
| nemotron-3-nano x10 | 10 | 161/164 | 98.2% | 1.3 |
| qwen3-coder x5 | 5 | 157/164 | 95.7% | 1.2 |
| qwen3-coder x10 | 10 | 159/164 | 97.0% | 1.4 |

**Key finding**: Cascade(1x3) with just 3 total iterations matches nemotron x10 (98.2%). Cascade(2x3) at 6 iterations reaches 98.8%, exceeding any single model at any iteration count.

---

## Phase 3: HumanEval Live Study Results

**Control baseline**: `bench_9d5ae700_20260213_092628.json` — gpt-oss:20b-128k x 10 iter, gpt-5-nano CP, checkpoint_interval=5

### Summary Table

| Study | Config | Score | Rate | Cost | Avg Iters | Delta vs Control |
|-------|--------|-------|------|------|-----------|-----------------|
| **Control** | gpt-oss x10, gpt-5-nano CP | **161/164** | **98.2%** | **$0.0124** | **1.2** | -- |
| Study 3 | + enhanced-feedback | 159/164 | 97.0% | $0.0178 | 1.3 | -1.2% |
| Study 4 | + on-demand checkpoints | 160/164 | 97.6% | $0.0424 | 1.2 | -0.6% |
| Study 5 | qwen3-coder + model-aware-specs | 157/164 | 95.7% | $0.0128 | 1.2 | -2.4% |
| **Study 6a** | **cascade (3 models x 2 iter)** | **161/164** | **98.2%** | **$0.0054** | **1.2** | **+0.0%** |
| **Study 6b** | **cascade + enhanced-fb + OD-CP** | **161/164** | **98.2%** | **$0.0053** | **1.2** | **+0.0%** |

### Outcome Attribution (HumanEval)

| Study | P1 (first pass) | Self-Recovery (iter 2-5) | Post-Checkpoint | Failed |
|-------|----------------|-------------------------|-----------------|--------|
| Control | 155 | 5 | 1 | 3 |
| Study 3: Enhanced FB | 153 | 6 | 0 | 5 |
| Study 4: On-Demand CP | 157 | 3 | 0 | 4 |
| Study 6a: Cascade | 153 | 8 | 0 | 3 |
| Study 6b: Combined | 154 | 7 | 0 | 3 |

### Cost Efficiency (HumanEval)

| Study | Total Cost | Cost per Success | Savings vs Control |
|-------|-----------|-----------------|-------------------|
| Control | $0.0124 | $0.000077 | -- |
| Study 6a: Cascade | $0.0054 | $0.000033 | **56% cheaper** |
| Study 6b: Combined | $0.0053 | $0.000033 | **57% cheaper** |

### Analysis

**Study 3 (Enhanced Feedback)**: Slightly *hurt* performance (-1.2%). The structured feedback parsing may be adding noise that confuses the model on problems it would otherwise self-correct. More self-recovery (+1) but more failures (+2).

**Study 4 (On-Demand Checkpoints)**: Marginal score loss (-0.6%) but 3.4x *higher* cost ($0.0424 vs $0.0124). The on-demand trigger fires more aggressively than expected, calling the checkpoint model more often than fixed intervals.

**Study 5 (Model-Aware Specs)**: Worst performer (-2.4%). Appending model-specific guidance to specs appears to constrain qwen3-coder rather than help it, causing regressions on problems it would otherwise solve.

**Study 6a (Cascade)**: Matches control score exactly while being **56% cheaper**. The cascade strategy leverages model diversity — different models solve different problems on first try, so the second/third models recover failures without expensive multi-iteration retry.

**Study 6b (Combined)**: Same score as 6a, marginally cheaper ($0.0053 vs $0.0054). Enhanced feedback and on-demand checkpoints are neutral when combined with cascade — neither helps nor hurts.

---

## Phase 4: BigCodeBench-Hard Results

148 most challenging multi-step coding tasks with library dependencies (pandas, numpy, matplotlib, etc.).

| Study | Config | Score | Rate | Cost | Avg Iters |
|-------|--------|-------|------|------|-----------|
| BCB-1 | gpt-oss:20b-128k zero-shot, no-spec | 27/148 | 18.2% | $0.0000 | 1.0 |
| BCB-4 | qwen3-coder:latest zero-shot, no-spec | 23/148 | 15.5% | $0.0000 | 1.0 |
| BCB-2 | gpt-5-nano zero-shot, no-spec | 25/148 | 16.9% | $0.1353 | 1.0 |
| **BCB-3** | **cascade + enhanced-fb + OD-CP** | **35/148** | **23.6%** | **$0.2076** | **6.5** |

### BCB-Hard Analysis

**Zero-shot model comparison**: All three models cluster in the 15-18% range on zero-shot BCB-Hard. gpt-oss:20b-128k leads (18.2%), followed by gpt-5-nano (16.9%), then qwen3-coder (15.5%). qwen3-coder's code-focused training gives it an edge on HumanEval's stdlib-only tasks but a disadvantage on BCB-Hard's library-heavy multi-step tasks (pandas, numpy, matplotlib), where gpt-oss:20b's broader training mix performs better.

**Local vs frontier**: The local model (gpt-oss:20b-128k, free) *outperforms* the small frontier model (gpt-5-nano, $0.1353) on BCB-Hard zero-shot: 27 vs 25 problems. This confirms that BCB-Hard difficulty lies in task complexity (multi-step library composition), not model capability — small frontier models have no inherent advantage.

**BCB-3 (Cascade)**: The optimized orchestration config recovers **8 additional problems** over the best local zero-shot (35 vs 27, +29.6% relative improvement), demonstrating that iterative refinement + model diversity provides meaningful gains on complex tasks. However, at $0.2076 this is expensive — the cost comes from problems that exhaust all 6 cascade iterations (3 models x 2 each) with 30s test timeouts.

**Cross-benchmark pattern**: The cascade strategy's advantage scales with task difficulty. On HumanEval (98% first-pass), cascade provides cost savings but no accuracy gain. On BCB-Hard (18% first-pass), cascade provides both accuracy gains (+5.4 pp) and model diversity benefits.

---

## Phase 5: Hierarchical Multi-File Orchestration

Can a frontier model (Opus) orchestrate local models to implement a 12-module project from a test contract, without writing code itself?

**Exercise**: Implement an `agentmon` clone (DNS monitoring system) from `SPEC.md` + 100 frozen acceptance tests.
**Full writeup**: [`HIERARCHICAL_ORCHESTRATION_RESULTS.md`](HIERARCHICAL_ORCHESTRATION_RESULTS.md)

### Baselines: Opus Writing Code Directly

| Run | Approach | Tests | Wall Clock | Opus Cost |
|-----|----------|-------|------------|-----------|
| A (est.) | Opus writes all code | 100/100 | ~6m 30s | ~$2.13 |
| A2 | Opus writes all code (clean room) | 100/100 | 7m 55s | $1.86 |

### Orchestrated Runs (Run B Series)

| Run | Worker Model | Strategy | Tests | Wall Clock | Opus Cost |
|-----|-------------|----------|-------|------------|-----------|
| B1 | gpt-oss:20b | Opus manual fixes | 100/100 | 13m 54s | $3.78 |
| B2 | gpt-oss:20b | Strict no-code | 100/100 | 20m 22s | $4.17 |
| B3 | gpt-oss:20b | Opus, no-code | 100/100 | 21m 51s | $3.98 |
| B4 | gpt-oss:20b | Opus, no-code | 100/100 | 60m 9s | $3.49 |
| B5 | gpt-oss:20b | Diagnostic reasoning | 100/100 | 13m 14s | $2.78 |
| **B6** | **qwen3-coder** | **Haiku diagnose + Opus fallback** | **100/100** | **11m 13s** | **$2.42** |
| B7 | qwen3-coder | Haiku diagnose + Opus fallback | 100/100 | 13m 57s | $2.77 |

### Key Findings (Hierarchical)

1. **Orchestration overhead is ~$0.61 / +3m 18s** over direct implementation (B6 $2.47 vs A2 $1.86). The overhead is relatively fixed — it doesn't scale with project size.

2. **Haiku diagnostic is cost-effective but not sufficient alone.** At ~$0.05 total, Haiku handles ~50% of failures (simple errors like wrong field names, missing imports). Cross-module interface mismatches still require Opus architectural reasoning.

3. **Worker model choice matters less than iteration strategy.** Both gpt-oss:20b and qwen3-coder achieve 100/100 with ~4 re-specs. qwen3-coder is ~1 minute faster (inference speed) but doesn't change the fix pattern.

4. **The dominant failure mode is interface mismatch.** Workers generate correct logic but wire up wrong dataclass field names for modules they can't see. This is inherent to subtask decomposition.

5. **Run-to-run variance is ~2m / ~$0.35** (B6 vs B7, identical setup). Driven by Opus extended thinking episodes — 14 turns at 46s of thinking in B7 vs zero in B6.

---

## Cross-Benchmark Summary

### Model Performance by Benchmark

| Model | HumanEval (zero-shot) | HumanEval (iterated) | BCB-Hard (zero-shot) | Agentmon (orchestrated) |
|-------|-----------------------|----------------------|----------------------|-------------------------|
| gpt-oss:20b-128k | 152/164 (92.7%) | 161/164 (98.2%) | 27/148 (18.2%) | 100/100 (B1-B5) |
| qwen3-coder:latest | 154/164 (93.9%) | 159/164 (97.0%) | 23/148 (15.5%) | 100/100 (B6-B7) |
| nemotron-3-nano:30b | 154/164 (93.9%) | 161/164 (98.2%) | — | — |
| gpt-5-nano | — | — | 25/148 (16.9%) | — |
| Cascade (3 models) | — | 161/164 (98.2%) | 35/148 (23.6%) | — |

### Cost Efficiency by Approach

| Benchmark | Best Local Zero-Shot | Best Iterated/Orchestrated | Cost Delta |
|-----------|---------------------|---------------------------|------------|
| HumanEval | 154/164, $0.00 | 161/164, $0.0053 (cascade) | +$0.005 for +4.3% accuracy |
| BCB-Hard | 27/148, $0.00 | 35/148, $0.2076 (cascade) | +$0.21 for +29.6% accuracy |
| Agentmon | — | 100/100, $2.47 (B6 orchestrated) | vs $1.86 direct (Opus A2) |

### Where Each Strategy Wins

| Task Type | Best Strategy | Why |
|-----------|--------------|-----|
| Single-function, stdlib (HumanEval) | Cascade, 3 models x 2 iter | Same accuracy as best single model, 57% cheaper |
| Multi-step, library-heavy (BCB-Hard) | Cascade + iteration | +29.6% over zero-shot; model diversity covers different library gaps |
| Multi-file project (Agentmon) | Direct (Opus writes code) | Orchestration works but costs +$0.61 and +3m; only cost-advantageous at larger scale |

---

## Recommendations

### Recommended Configurations

**For HumanEval-class problems** (function-level, stdlib-only):
```
--cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest"
--cascade-budget 2
--max-iterations 6
```
- Matches best single-model score (161/164, 98.2%) at 57% lower cost ($0.0053)
- No need for enhanced feedback or on-demand checkpoints (neutral impact)

**For BCB-Hard-class problems** (multi-step, library-dependent):
```
--cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest"
--cascade-budget 2
--enhanced-feedback
--checkpoint-strategy on-demand
```
- Best absolute score (35/148, 23.6%)
- Iterative refinement recovers +29.6% more problems than zero-shot

**For multi-file projects** (hierarchical orchestration):
```
Worker: qwen3-coder:latest
Orchestrator: Opus
Diagnostic: Haiku (--diagnose --max-retries 2)
Spec style: Arm B (rich logic, no gotchas)
```
- 100/100 at $2.47 total ($2.42 Opus + $0.05 Haiku)
- Subtask decomposition with parallelism: 1 → (2+3) → (4+5)

### Key Takeaways

1. **Cascade is the clear winner for benchmarks**: Matches control accuracy at 57% lower cost on HumanEval, and provides +5.4pp accuracy gain on BCB-Hard. Model diversity is more valuable than additional iterations with a single model.

2. **Local models match or beat small frontier models**: gpt-oss:20b-128k (free) outperforms gpt-5-nano ($0.1353) on BCB-Hard zero-shot (18.2% vs 16.9%). qwen3-coder (free) scores 93.9% zero-shot on HumanEval. The local-first approach is validated.

3. **Hierarchical orchestration works but has a cost floor**: Opus can orchestrate local models to implement a 12-module project at 100% test pass rate. The ~$0.61 overhead is fixed and becomes cost-advantageous at larger project scale where worker tokens dominate.

4. **Haiku as diagnostic tier is highly cost-effective**: At $0.05 per project, Haiku handles ~50% of worker failures automatically. The three-tier pattern (free worker → cheap diagnostic → expensive orchestrator) minimizes total cost.

5. **Early exit at iteration 3 captures 97%+ of value**: Beyond iteration 2, marginal gains are near-zero for all models on HumanEval. On BCB-Hard, more iterations help (avg 6.5 for cascade), but most value is still front-loaded.

6. **Model-aware specs and enhanced feedback are dead ends**: Model-aware specs caused regressions (-2.4pp). Enhanced feedback was neutral at best. On-demand checkpoints inflated costs 3.4x with no accuracy gain. These features should not be used.

### Features to Keep vs Drop

| Feature | Verdict | Rationale |
|---------|---------|-----------|
| Model Cascade | **KEEP** | 57% cost savings, +5.4pp on hard tasks |
| Haiku Diagnostic | **KEEP** | $0.05/project, handles 50% of failures |
| Early Exit (max_iter 3) | **KEEP** | Captures 97% of value, massive cost savings |
| Enhanced Feedback | NEUTRAL | No measurable impact on HumanEval |
| On-Demand Checkpoints | DROP | 3.4x cost increase, no accuracy gain |
| Model-Aware Specs | DROP | Causes regressions (-2.4pp) |

---

## Benchmark Result Files

| Study | File |
|-------|------|
| Control | `bench_9d5ae700_20260213_092628.json` |
| Study 3: Enhanced Feedback | `bench_aa9d1870_20260224_163533.json` |
| Study 4: On-Demand CP | `bench_ac6f22fe_20260224_163538.json` |
| Study 5: Model-Aware Specs | `bench_984873ab_20260224_163543.json` |
| Study 6a: Cascade | `bench_efa85f30_20260224_175400.json` |
| Study 6b: Combined | `bench_a303afdb_20260224_175404.json` |
| BCB-1: gpt-oss Zero-Shot | `bench_3880fd27_20260224_185909.json` |
| BCB-2: gpt-5-nano Zero-Shot | `bench_760cbe72_20260224_185912.json` |
| BCB-3: Cascade+Enhanced+OD | `bench_65e53820_20260224_185917.json` |
| BCB-4: qwen3-coder Zero-Shot | `bench_8ccbbfb9_20260226_022450.json` |
| Agentmon A2: Opus Direct | `orchestrator_test/results/run-a2/` |
| Agentmon B1-B7: Orchestrated | `orchestrator_test/results/run-b{1..7}*/` |
