# Hierarchical Orchestration Experiment Results

Can a frontier model (Opus) orchestrate local models to implement a multi-file project from a test contract, without writing code itself?

**Exercise**: Implement an `agentmon` clone (DNS monitoring system) from `SPEC.md` + 100 frozen acceptance tests. The orchestrator writes specs and reviews; worker models write all code.

**Run dates**: 2026-02-25 to 2026-02-26
**Ollama server**: 192.168.1.74:11434 (2x RTX 3090)
**Test target**: 100/100 acceptance tests (`tests/test_agentmon_acceptance.py`)
**Data location**: `orchestrator_test/results/`

---

## Baselines: Opus Writing Code Directly (Run A)

| Run | Approach | Tests | Wall Clock | Opus Cost |
|-----|----------|-------|------------|-----------|
| A (est.) | Opus writes all code | 100/100 | ~6m 30s | ~$2.13 |
| A2 | Opus writes all code (clean room) | 100/100 | 7m 55s | $1.86 |

In Run A/A2, Opus reads the test file and SPEC.md, then writes all 12+ modules itself in a single pass with iterative test-fix cycles. No local models involved. This is the cost/time floor for "just do it yourself."

---

## Run B Series: Orchestrated Implementation

All Run B experiments use the same prompt:
> "Read RUN_B_INSTRUCTIONS.md and SPEC.md, then implement the agentmon clone using the orchestrated approach. Delegate all coding to local models via scripts/orchestrate_subtask.py."

### Summary Table

| Run | Worker Model | Iteration Strategy | Tests | Wall Clock | Opus Cost | Notes |
|-----|-------------|-------------------|-------|------------|-----------|-------|
| B1 | gpt-oss:20b | Opus manual fixes | 100/100 | 13m 54s | $3.78 | First successful orchestration |
| B2 | gpt-oss:20b | Opus manual fixes (strict no-code) | 100/100 | 20m 22s | $4.17 | Stricter no-code policy slowed it |
| B3 | gpt-oss:20b | Opus, no-code policy | 100/100 | 11m 27s | $3.98 | |
| B4 | gpt-oss:20b | Opus, no-code policy | 100/100 | 12m 40s | $3.49 | Got stuck in long fix loops |
| B5 | gpt-oss:20b | Opus diagnostic reasoning | 100/100 | 13m 14s | $2.78 | Breakthrough: spec reuse + parallel |
| **B6** | **qwen3-coder** | **Haiku auto-diagnose + Opus fallback** | **100/100** | **11m 13s** | **$2.42** | **Best run** |
| B7 | qwen3-coder | Haiku auto-diagnose + Opus fallback | 100/100 | 13m 57s | $2.77 | Same setup, higher variance |

### Evolution of Approach

**B1-B2**: Opus writes specs, calls `orchestrate_subtask.py`, reads failures, writes fix specs. All diagnostic reasoning done by Opus. Works but expensive — Opus spends most of its tokens analyzing test output and writing fix specs.

**B3-B4**: Attempted stricter delegation. B3-codex tried using Codex as the orchestrator (failed — couldn't manage the multi-step workflow). B4 got stuck in extended fix loops on subtask 2, burning 60 minutes on what should take ~10.

**B5**: Key improvements — reused existing spec files instead of rewriting them, ran subtask pairs in parallel (2+3, 4+5) exploiting both GPUs, and refined diagnostic reasoning. Cut time from 20m+ to 13m and cost from $3.98 to $2.78.

**B6-B7**: Two changes: (1) switched worker from gpt-oss:20b to qwen3-coder:latest, (2) added `--diagnose` flag that calls Haiku to auto-diagnose test failures and generate fix specs, removing that cost from Opus. B6 achieved the best result: 11m 13s at $2.42.

---

## B6 Deep Dive (Best Run)

### Per-Subtask Breakdown

| Subtask | Tests | 1st Try | Final | Worker Calls | Fix Method |
|---------|-------|---------|-------|-------------|------------|
| 1: Data models + storage | 18/18 | 14/18 | 18/18 | 2 | Haiku auto-diagnose |
| 2a: Syslog + parsers | 17/17 | 0/17 | 17/17 | 3 | 1 re-spec + 1 manual |
| 2b: Detection engine | 28/28 | 23/28 | 28/28 | 4 | 2 auto-diagnose + 2 manual |
| 3a: LLM classifier | 15/15 | 8/15 | 15/15 | 3 | 1 re-spec + 1 manual |
| 3b: CLI + alerting | 18/18 | 17/18 | 18/18 | 2 | Haiku auto-diagnose |
| Integration | 100/100 | 99/100 | 100/100 | 1 | 1 manual (timestamp fix) |

### Token Usage

- **Worker (qwen3-coder)**: 34K prompt + 26K completion (~10min GPU time, $0.00)
- **Haiku diagnostic**: 45K prompt + 3.3K completion (~$0.05)
- **Opus orchestrator**: ~7K output tokens ($2.42)
- **Escalations**: 4 re-specs (Level 1), 0 take-overs (Level 3)

### What Haiku Diagnostic Solved vs Didn't

**Haiku fixed** (subtasks 1, 5, partially 3): Simple errors like wrong field names in dataclass constructors, missing imports, off-by-one logic. Haiku correctly diagnosed the test failure and wrote a 10-20 line fix spec that qwen3-coder could execute.

**Haiku couldn't fix** (subtasks 2, 4): Cross-module interface mismatches (syslog parser using wrong DNSEvent field names), circular imports, async handler patterns. These required Opus to analyze the architectural mismatch and write a more targeted re-spec.

---

## Key Findings

### 1. Orchestration overhead is ~$0.50-1.00 over direct implementation

| Approach | Cost | Time | Code Author |
|----------|------|------|-------------|
| Opus direct (A2) | $1.86 | 7m 55s | Opus |
| Orchestrated best (B6) | $2.42 + $0.05 Haiku | 11m 13s | qwen3-coder (free) |
| **Overhead** | **+$0.61** | **+3m 18s** | |

The orchestration tax is the cost of Opus reading specs, planning subtask decomposition, and handling failures that Haiku can't resolve. This overhead is relatively fixed — it doesn't scale with problem size.

### 2. Worker model choice matters less than iteration strategy

qwen3-coder and gpt-oss:20b both achieve 100/100 with similar fix patterns. The main difference is first-try hit rate on individual subtasks, but both need ~4 re-specs to reach 100%. The switch to qwen3-coder in B6 saved ~1 minute (faster inference) but didn't change the fix pattern.

### 3. Haiku diagnostic is cost-effective but not sufficient alone

At ~$0.05 total, Haiku handles ~50% of failures automatically. The remaining failures (cross-module interface mismatches) require the orchestrator's architectural understanding. This matches the B5 finding that "diagnostic reasoning is load-bearing, not overhead."

### 4. The dominant failure mode is interface mismatch

Across all B runs, the most common worker error is **using wrong field names for dataclasses defined in other modules**. The worker generates correct logic but wires up the wrong interface. This is inherent to the subtask decomposition approach — each worker only sees its own spec, not the full codebase.

### 5. Variance between identical runs is ~2 minutes / ~$0.35

B6 ($2.42, 11m 13s) vs B7 ($2.77, 13m 57s) used identical code and instructions. The difference came from Opus spending 46s in extended thinking during B7's integration phase (diagnosing a timestamp issue). This variance sets the floor for further optimization.

---

## Comparison: Orchestrated vs Direct, by Task Complexity

| Task Type | Direct (Opus) | Orchestrated (Opus + local) | Winner |
|-----------|--------------|---------------------------|--------|
| HumanEval (single function) | ~$0.01/task | N/A (overkill) | Direct |
| Agentmon (100-test, 12-module) | $1.86 | $2.47 | Direct (but close) |
| Hypothetical 500-test project | Scales linearly with Opus tokens | Fixed orchestration + free worker tokens | Orchestrated |

The orchestrated approach becomes cost-advantageous when worker tokens dominate — i.e., larger projects where the implementation cost (free local tokens) dwarfs the fixed orchestration overhead (~$2.50).

---

## Infrastructure

### Scripts

- `scripts/orchestrate_subtask.py` — Worker call + file extraction + test run in one command
- `scripts/ollama_worker.py` — Raw Ollama API wrapper
- `scripts/run_with_cost_tracking.sh` — Wraps Claude Code session, captures cost from status bar

### Key Flags

- `--diagnose` — Haiku auto-diagnoses test failures and generates fix specs ($0.01/call)
- `--diagnose-model` — Default: `claude-haiku-4-5-20251001`
- `--max-retries` — Diagnostic retry attempts (default: 2)
- `--context` — Injects current file contents into worker prompt (no Opus token cost)

### Configuration

- **Worker model**: qwen3-coder:latest (default in B6+)
- **Spec style**: Arm B (rich logic, no gotchas) — best for qwen3-coder
- **Subtask decomposition**: 5 subtasks with parallelism: 1 → (2+3) → (4+5)
- **Instructions**: `RUN_B_INSTRUCTIONS.md`
