# Orchestration Improvement Studies — Work Plan

## Status: Code Complete, Ready for Live Studies

All 6 features have been implemented and verified. The simulation analysis has been run.
This document captures what to do next once Ollama and API keys are ready.

---

## Prerequisites Checklist

Before running live studies, ensure:

- [ ] Ollama is running (`ollama serve`)
- [ ] Models loaded:
  - `ollama pull gpt-oss:20b-128k`
  - `ollama pull nemotron-3-nano:30b`
  - `ollama pull qwen3-coder:latest`
- [ ] API keys set in `.env` or environment:
  - `ANTHROPIC_API_KEY=sk-ant-...`
  - `OPENAI_API_KEY=sk-proj-...`
- [ ] `CORTEX_PATH` set to your cortex-core dist/index.js
- [ ] `poetry install` has been run

---

## What Was Already Done

### Phase 1: Simulation Studies (COMPLETE)

Run `python studies/orchestration_improvements.py` — results already in `docs/ORCHESTRATION_STUDY_RESULTS.md`.

Key findings:
- **Early Exit**: gpt-oss captures 97% (159/164) at iteration 2, only +2 more by iteration 15
- **Cascade(2×3)**: 162/164 (98.8%) with 6 total iterations — exceeds any single model at 10 iters

### Phase 2: Feature Implementation (COMPLETE)

6 features implemented across 4 files:

| Feature | Files Modified | CLI Flag |
|---------|---------------|----------|
| Enhanced Test Feedback | `humaneval.py`, `orchestrator.py` | `--enhanced-feedback` |
| On-Demand Checkpoints | `orchestrator.py` | `--checkpoint-strategy on-demand` |
| Model Cascade | `orchestrator.py` | `--cascade-models M1,M2,M3 --cascade-budget N` |
| Model-Aware Specs | `registry.py`, `orchestrator.py` | `--model-aware-specs` |
| Early Exit | (already existed as `--max-iterations`) | `--max-iterations 3` |
| Attribution Analysis | `studies/orchestration_improvements.py` | `--include-live` |

---

## What To Do Next

### Step 1: Verify CLI flags work

```bash
poetry run koderz benchmark --help
# Confirm you see: --enhanced-feedback, --checkpoint-strategy, --cascade-models,
#                   --cascade-budget, --model-aware-specs
```

### Step 2: Quick smoke test (1 problem)

```bash
# Test enhanced feedback
poetry run koderz run --problem-id "HumanEval/0" \
  --local-model "gpt-oss:20b-128k" \
  --max-iterations 3 \
  --enhanced-feedback \
  --debug --debug-dir ./debug

# Test cascade
poetry run koderz run --problem-id "HumanEval/0" \
  --cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b" \
  --cascade-budget 2 \
  --debug --debug-dir ./debug

# Test on-demand checkpoints
poetry run koderz run --problem-id "HumanEval/54" \
  --local-model "gpt-oss:20b-128k" \
  --max-iterations 10 \
  --checkpoint-strategy on-demand \
  --debug --debug-dir ./debug
```

### Step 3: Run Phase 3 — HumanEval Live Studies (~3 hours)

```bash
./studies/run_orchestration_studies.sh
```

This runs 5 controlled experiments on all 164 HumanEval problems:

| Study | Config | What it tests |
|-------|--------|---------------|
| 3 | `--enhanced-feedback --max-iterations 10` | Does structured feedback improve iter-2 rate? |
| 4 | `--checkpoint-strategy on-demand --max-iterations 10` | Same score at lower checkpoint cost? |
| 5 | `--model-aware-specs --local-model qwen3-coder:latest --max-iterations 5` | Fewer qwen3 regressions? |
| 6a | `--cascade-models gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest --cascade-budget 2` | Same score with fewer iterations? |
| 6b | Combined: cascade + enhanced-feedback + on-demand CP | Best overall config? |

Control baseline: `bench_9d5ae700_20260213_092628.json` (gpt-oss × 10 iter, gpt-5-nano CP = 161/164 at $0.012)

### Step 4: Analyze HumanEval results

```bash
python studies/orchestration_improvements.py --include-live
```

This updates `docs/ORCHESTRATION_STUDY_RESULTS.md` with live study comparison tables.

### Step 5: Run Phase 4 — BigCodeBench-Hard Studies (~2 hours)

```bash
# First ensure BCB-Hard data is downloaded
poetry run koderz download-data --dataset bigcodebench-hard

# Then run studies
./studies/run_bigcodebench_studies.sh
```

This runs 3 experiments on 148 BCB-Hard tasks:

| Run | Config | Purpose |
|-----|--------|---------|
| BCB-1 | gpt-oss × zero-shot, no-spec | Baseline local model capability |
| BCB-2 | gpt-5-nano × zero-shot | Frontier reference |
| BCB-3 | Best config from Phase 3 | Apply optimized orchestration |

### Step 6: Final analysis

```bash
python studies/orchestration_improvements.py --include-live
```

Review `docs/ORCHESTRATION_STUDY_RESULTS.md` for:
- Per-study results table (score, cost, avg iterations, improvement delta)
- HumanEval vs BCB-Hard pattern comparison
- Recommended production configuration

---

## File Inventory

### Created
- `studies/orchestration_improvements.py` — simulation + live analysis
- `studies/run_orchestration_studies.sh` — HumanEval study runner
- `studies/run_bigcodebench_studies.sh` — BCB-Hard study runner
- `docs/ORCHESTRATION_STUDY_RESULTS.md` — generated report (simulation results already populated)

### Modified
- `koderz/models/registry.py` — added `spec_guidance` field, `MODEL_SPEC_GUIDANCE`, `get_spec_guidance()`
- `koderz/benchmarks/humaneval.py` — added `enhance_test_feedback()`
- `koderz/orchestrator.py` — added `_detect_stuck_pattern()`, `_run_cascade()`, new init params, on-demand CP logic, enhanced feedback integration, model-aware spec generation
- `koderz/cli.py` — 5 new flags on both `run` and `benchmark` commands, all orchestrator instantiations updated
