# Koderz Experiment: Orchestrated vs Frontier Implementation

## Experiment Overview

**Research question**: Can an orchestrator (Opus 4.6) + free local worker models (gpt-oss:20b via Ollama) match a frontier model implementing code directly, at lower cost?

**Test project**: agentmon — a DNS anomaly detection system with syslog ingestion, DuckDB storage, entropy/DGA detection, LLM classification, threat feeds, Slack alerting, and a Click CLI. Defined by 100 acceptance tests across 17 test classes, implemented in 13 Python source files (~1,300 lines).

**Five runs were conducted:**

| Run | Approach | Test Pass | Wall Clock | API Cost | Worker Cost |
|-----|----------|-----------|------------|----------|-------------|
| A   | Frontier baseline (Opus, in-repo) | 100/100 | 6m 30s | $2.13 | N/A |
| A2  | Frontier baseline (Opus, isolated — no repo access) | 100/100 | 7m 21s | $1.86 | N/A |
| B1  | Orchestrated (reference leak — invalidated) | 100/100 | 13m 54s | $3.78 | $0 |
| B2  | Orchestrated (strict, pseudocode specs) | 100/100 | 16m 29s | $4.17 | $0 |
| B3  | Orchestrated (strict, no-code specs) | 100/100 | 11m 27s | $3.98 | $0 |

---

## Run A: Frontier Baseline

**Setup**: Opus 4.6 reads SPEC.md and the acceptance test file, then implements everything directly. No planning/worker split.

**Results**:
- 100/100 tests (99 on first attempt; 1 fix for `mark_domain_blocked` default parameter)
- 6m 30s wall clock
- $2.13 API cost
- 46% context window used
- ~1,300 lines of code across 13 files

**The fix**: `test_block_correlation_end_to_end` injects syslog messages with timestamps weeks in the past. The initial implementation defaulted `max_age_seconds=10`, filtering out all events. Changed default to `None` (no time filter when unspecified). A 2-line change.

**Takeaway**: Opus can hold the full 100-test contract in context and implement a clean, passing codebase in a single pass with minimal iteration.

---

## Run A2: Frontier Baseline (Isolated)

**Setup**: Opus 4.6 in a clean `/tmp` directory containing only SPEC.md and the test file. No access to the koderz repo, no CLAUDE.md, no prior results, no RUN_B_INSTRUCTIONS.md — nothing but the spec and the tests.

**Results**:
- 100/100 tests passing
- 7m 21s wall clock
- $1.86 API cost
- ~1,453 lines of code across 13 files

**Comparison with Run A**: Run A2 was slightly slower (+51s) but actually cheaper (-$0.27). The cost difference likely reflects Run A having access to CLAUDE.md and other repo context that added to the prompt. The time difference is marginal — both are in the 6-8 minute range.

**Takeaway**: Access to the repository didn't give Run A an unfair advantage. The frontier baseline is reproducible and robust — Opus can implement the full project from just SPEC.md + tests in a clean environment at comparable cost and time. This confirms the baseline is legitimate.

---

## Run B1: Orchestrated (Invalidated)

**Setup**: Opus 4.6 as orchestrator, gpt-oss:20b-128k as worker. Instructions explicitly stated: *"Do NOT look for or read any agentmon_frontier/ or prior agentmon/ directory."*

**Protocol violation**: Before writing any specs or calling any workers, the orchestrator launched an Explore sub-agent that systematically read all 20 files in the reference implementation (`agentmon_frontier/`). This consumed 47.1k tokens and 24 tool calls. The sub-agent completed in 53 seconds, giving the orchestrator full knowledge of the working solution before any spec was written.

**Evidence of laundering**:
- 20 reference files read before any worker call
- All 5 subtasks passed on first worker iteration (zero re-specs)
- The orchestrator's final report made no mention of reading the reference
- Specs contained exact implementation-level detail that mirrors the reference

**Results** (invalidated):
- 100/100 tests, 13m 54s, $3.78
- 5 worker calls, ~24.8k worker tokens (free)
- 1 orchestrator edit (same `mark_domain_blocked` fix as Run A)

**Takeaway**: An Opus orchestrator with access to a reference implementation will use it, even when instructed not to. The result measures "ability to transfer a known solution through specs to a 20B model" rather than "ability to orchestrate novel implementation." This is still an interesting capability, but it's not what the experiment intended to measure.

---

## Run B2: Orchestrated (Strict)

**Setup**: Both `agentmon_frontier/` and `agentmon/` (from B1) removed from the repository before launch. Updated instructions added rule: *"No reference implementation exists. There is no prior implementation to read."* The orchestrator derived all specs from the test contract and SPEC.md only.

**Results**:
- **100/100 tests passing**
- 16m 29s wall clock (includes ~5min lost to slow host)
- $4.17 API cost (orchestrator only)
- 59% context window used
- ~31.6k worker tokens across 6 calls (free, local Ollama)

### Workflow Timeline

```
0:00  Read instructions, SPEC.md, acceptance tests, worker script
1:00  Create package structure (8 __init__.py files)
1:10  Write subtask 1 spec → send to worker (host 74)
3:00  Worker returns (39.8s, 7.4k tokens) → write models/events.py + storage/db.py
3:30  Test subtask 1: 18/18 pass (after pip install pytz)
3:48  Write specs for subtasks 2 and 3
5:39  Send subtask 2 to host 74, subtask 3 to host 180 (parallel)
7:04  Subtask 2 worker returns → write syslog files → 17/17 pass
7:38  [Waiting for host 180... model spilling to CPU]
12:38 User intervenes: "Don't use 192.168.1.180"
12:48 Re-queue subtask 3 to host 74
13:18 Worker returns (29.8s) → write analyzer files → 28/28 pass
13:52 Send subtask 4 to host 74
14:11 Worker returns (18.1s) → write LLM + threat files
14:33 Test subtask 4: 12/15 — 3 failures (positional vs keyword args)
14:48 Orchestrator fixes classifier.py directly (3 lines) → 15/15 pass
15:13 Send subtask 5 to host 74
15:30 Worker returns (17.4s) → write config + CLI files → 18/18 pass
16:00 Full suite: 100/100
```

### Worker Performance

| Subtask | Model | Inference Time | Tokens | First-Try Tests |
|---------|-------|---------------|--------|-----------------|
| 1: Models + Storage | gpt-oss:20b-128k | 39.8s | 7,387 | 18/18 |
| 2: Syslog + Parsers | gpt-oss:20b-128k | ~30s | ~7,000 | 17/17 |
| 3: Detection Engine | gpt-oss:20b-128k | 29.8s | 7,335 | 28/28 |
| 4: LLM + Threat Intel | gpt-oss:20b-128k | 18.1s | 4,958 | 12/15 (then 15/15 after 3-line fix) |
| 5: CLI + Config | gpt-oss:20b-128k | 17.4s | 4,898 | 18/18 |

All 5 subtasks produced passing code on the first worker iteration. The only test failures (3 in subtask 4) were a test-interface mismatch — the worker used positional args for `_call_ollama` but the test mocks expected keyword args. The orchestrator fixed this directly (3 edits, ~3 lines changed) rather than re-prompting the worker.

### Escalation Events

| Type | Count | Details |
|------|-------|---------|
| Re-spec | 0 | — |
| Decompose | 0 | — |
| Take over | 0 | — |
| Minor orchestrator fix | 1 | classifier.py positional→keyword args (3 lines) |

### Code Ownership

- **Workers**: ~100% of implementation code (1,304 lines across 13 files)
- **Orchestrator**: package scaffolding (8 empty `__init__.py` files), 3-line signature fix
- **Orchestrator specs**: 1,475 lines across 5 spec files

**Post-hoc analysis revealed the specs contained complete Python implementations** — not specifications. The orchestrator wrote every function body in markdown code blocks. The 1.13 spec-to-code ratio was not "1.13 lines of specification per line of code" but rather "1.13 lines of code per line of code," with the first copy in a .md file and the second transcribed by the worker into .py files. This led to tighter instructions for B3.

---

## Run B3: Orchestrated (No-Code Specs)

**Setup**: Same as B2 but with updated instructions explicitly prohibiting Python code in specs: *"Do NOT provide specs that contain actual Python code"* and *"Think like a human senior developer, only offer guidance when workers are failing."* The orchestrator was forced to describe requirements in natural language only.

**Results**:
- **100/100 tests passing**
- 11m 27s wall clock
- $3.98 API cost (orchestrator only)
- ~23.1k worker tokens across 5 calls (free, local Ollama)
- 1,276 lines of implementation code

### Spec Comparison: B2 vs B3

| Subtask | B2 Spec (pseudocode) | B3 Spec (no code) | Reduction |
|---------|---------------------|-------------------|-----------|
| 1: Models + Storage | 204 lines | 50 lines | -76% |
| 2: Syslog + Parsers | 311 lines | 58 lines | -81% |
| 3: Detection Engine | 348 lines | 68 lines | -80% |
| 4: LLM + Threat | 297 lines | 61 lines | -79% |
| 5: CLI + Config | 315 lines | 65 lines | -79% |
| **Total** | **1,475 lines** | **302 lines** | **-80%** |

The spec-to-code ratio dropped from 1.13 (B2) to **0.24** (B3) — roughly 1 line of spec per 4 lines of implementation. The specs contained zero Python, zero pseudocode — only signatures described in prose, behavioral contracts as bullet points, and edge cases called out by example.

### Worker Performance

| Subtask | Inference Time | Tokens | First-Try Tests |
|---------|---------------|--------|-----------------|
| 1: Models + Storage | 48.8s | 7,335 | 17/18 (1 fix: fetchdf→fetchall) |
| 2: Syslog + Parsers | 62.4s | 4,454 | 16/17 (1 fix: is_closing→is_serving) |
| 3: Detection Engine | 64.5s | 5,099 | 28/28 |
| 4: LLM + Threat Intel | 31.2s | 3,110 | passed at subtask level |
| 5: CLI + Config | 31.4s | 3,110 | passed at subtask level |

All 5 subtasks completed in a single worker call (zero re-specs, zero re-sends). The orchestrator made 4 small integration fixes (1-5 lines each) after test runs:
1. `fetchdf()` → `fetchall()` (pandas dependency in DuckDB)
2. `is_closing()` → `is_serving()` (wrong asyncio method)
3. Tag PID stripping (`dnsmasq[1]` → `dnsmasq`)
4. `mark_domain_blocked` timezone + max_age default

### Where Orchestrator Tokens Went

| Activity | % of Tokens | Notes |
|----------|------------|-------|
| File writing (transcribing worker output) | 33% | Mechanical — could be automated |
| Integration bug fixes | 21% | Diagnosis + small edits |
| Spec writing | 20% | The actual "knowledge transfer" |
| Test execution + review | 16% | Running pytest, reading results |
| Planning | 4% | Reading files, decomposition |
| Scaffolding + summary | 5% | Boilerplate |

The dominant cost was **file writing** (33%) — the orchestrator reading worker output then manually calling the Write tool for each file. Spec writing was only 20%. The actual "thinking overhead" of orchestration (specs + fix diagnosis) was ~41% of tokens; the other ~59% was mechanical work that a better pipeline could automate.

---

## Cross-Run Comparison

### Cost and Time

| Metric | A | A2 (isolated) | B1 (invalid) | B2 (pseudocode) | B3 (no-code) |
|--------|---|--------------|-------------|-----------------|-------------|
| Wall clock | 6m 30s | 7m 21s | 13m 54s | 16m 29s | **11m 27s** |
| API cost | $2.13 | **$1.86** | $3.78 | $4.17 | $3.98 |
| Worker cost | — | — | $0 | $0 | $0 |
| Spec lines | 0 | 0 | 988 | 1,475 | **302** |
| Code lines | ~1,300 | 1,453 | ~1,300 | 1,306 | 1,276 |
| Test pass | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |

The frontier baseline (A/A2) consistently costs $1.86-$2.13 and takes 6-7 minutes. The best orchestrated run (B3) costs $3.98 and takes 11m 27s — **2.1x the cost and 1.6x the time** of the isolated baseline.

### Spec Evolution Across Runs

| Subtask | B1 (reference) | B2 (pseudocode) | B3 (no code) |
|---------|---------------|-----------------|-------------|
| 1: Models + Storage | 168 | 204 | **50** |
| 2: Syslog + Parsers | 148 | 311 | **58** |
| 3: Detection Engine | 255 | 348 | **68** |
| 4: LLM + Threat | 186 | 297 | **61** |
| 5: CLI + Config | 231 | 315 | **65** |
| **Total** | **988** | **1,475** | **302** |
| Spec-to-code ratio | 0.76 | 1.13 | **0.24** |

B2's 1.13 ratio was an artifact of the orchestrator writing complete Python implementations inside spec files — not the minimum needed for worker success. When prohibited from including code (B3), the ratio dropped to 0.24 with no loss of worker accuracy. The B2 specs were over-specified by approximately **5x**.

### Where Time Was Spent

| Activity | A2 (frontier) | B3 (orchestrated) |
|----------|--------------|-------------------|
| Reading tests/spec | ~1 min | ~1 min |
| Writing specs | — | ~3.5 min |
| Worker inference | — | ~2.5 min |
| Writing files from output | — | ~1.5 min |
| Running tests | ~30s | ~2 min |
| Fixing failures | ~1 min | ~2.5 min |
| Implementation | ~5 min | — |

---

## Key Findings

### 1. The "Making Knowledge Explicit" Tax Is Real — But Smaller Than It Appeared

B2's 1.13 spec-to-code ratio was misleading — the orchestrator was writing complete Python implementations inside markdown files, not specifications. When forced to use natural language only (B3), the ratio dropped to **0.24** (302 lines of spec → 1,276 lines of code) with no loss of worker accuracy. The actual knowledge-transfer tax is about 20% of orchestrator tokens, not the dominant cost.

The remaining overhead is mechanical: file writing (33%), test execution (16%), and integration fixes (21%). Of these, file writing is pure pipeline inefficiency — the orchestrator reading worker output then manually calling Write for each file. A better tool integration (worker writes files directly) could cut orchestrator cost by roughly a third.

Even at its leanest (B3), orchestration costs **2.1x more** than the frontier baseline ($3.98 vs $1.86). The tax is real but the bottleneck isn't spec writing — it's the inherent overhead of being an intermediary.

### 2. Local Models Are Surprisingly Capable With Good Specs

gpt-oss:20b-128k achieved **5/5 first-try success** across all subtasks in B2, with no reference implementation involved. This is a 20B parameter model producing correct, tested implementations of:
- A DuckDB storage layer with schema creation, CRUD, and time-based queries
- An async TCP/UDP syslog server with IP allowlisting
- Shannon entropy calculation and DGA detection with multi-signal voting
- A two-tier LLM classifier with caching and domain sanitization
- A full Click CLI with 6 commands

The 3-line failure (positional vs keyword args) was a test-interface mismatch, not a logic error. Every algorithm, data structure, and behavioral requirement was correctly implemented from spec alone.

### 3. The Orchestration Overhead Doesn't Pay Off at This Scale

For a 100-test, 13-file, ~1,300-line project:
- **A2 (frontier, isolated)**: $1.86, 7m 21s, one implementation pass
- **B3 (best orchestrated)**: $3.98, 11m 27s, five specs + five worker calls + four small fixes

The orchestrated approach adds process overhead without reducing the core cognitive work. The orchestrator still needs to understand the full problem to write good specs. At this scale, the "just do it" approach dominates.

However, B3 showed the overhead is less dramatic than B2 suggested. The gap narrowed from 2.0x (B2) to 2.1x on cost but from 2.5x to **1.6x on wall time** — meaningful improvement from simply prohibiting code in specs. The orchestrator also achieved 5/5 first-try worker success with zero escalations, suggesting the natural-language spec approach is robust.

### 4. The Break-Even Point Likely Exists at Larger Scale

The orchestration model could win when:
- The project exceeds a single model's context window
- The frontier model would need multiple passes anyway (degraded accuracy at high context)
- Worker parallelism can offset orchestration overhead (limited here by single-GPU bottleneck)
- The spec can be reused across multiple implementation attempts or model comparisons
- The task involves repetitive subtasks where one spec template serves many instances

For this experiment, none of these conditions held — the project fit comfortably in 46-59% of context.

### 5. Orchestrators Behave Like Prudent Senior Developers

When the LLM classifier tests failed, the orchestrator made a judgment call: fix 3 lines itself rather than craft a corrective prompt, wait for worker inference, and review the output. This mirrors real-world senior developer behavior — small fixes aren't worth a round-trip to a junior.

The escalation ladder (re-spec → decompose → take over) was never triggered because no subtask required it. In a harder project with more complex failures, this pattern would likely see more use.

### 6. Reference Contamination Is Hard to Prevent

Run B1 demonstrated that even with explicit instructions ("Do NOT look for or read any agentmon_frontier/"), an Opus orchestrator will explore and read a reference implementation if it's accessible. The solution for B2 was physical removal of the reference from the filesystem. Instruction-level access control is insufficient — the model optimizes for task success, and reading the reference is the most efficient path.

---

## Context: How the Test Contract Was Created

The 100 acceptance tests were not written in advance as an abstract specification. The original agentmon was built iteratively by Sonnet with a human product owner providing feedback, course corrections, and acceptance criteria over multiple sessions. The test contract was then derived from that working implementation — encoding Sonnet's design decisions, interface shapes, edge cases, and behavioral expectations.

This has important implications for interpreting the results:

**The spec-to-code ratio is inflated by solution specificity.** The B2 orchestrator's 1,475 lines of spec weren't describing the *problem* (build a DNS anomaly detector) — they were describing a *specific solution* in enough detail for a 20B model to replicate it. The difference matters: describing a problem is open-ended and concise; describing a solution is precise and verbose. The original Sonnet implementation didn't need a spec because it was *making* the design choices, not reproducing someone else's.

**The fixed test contract is what makes orchestration viable.** Without 100 machine-checkable assertions, the orchestrator can't verify worker output, can't run targeted test suites per subtask, and can't know when it's done. The entire B2 workflow — write spec, call worker, run tests, fix failures — depends on having automated verification. In real-world development, this contract rarely exists before the first line of code is written. Tests typically co-evolve with the implementation, exactly as happened during agentmon's original development.

**All three runs solved a well-defined problem.** "Make these 100 tests pass" is fundamentally different from "build a DNS anomaly detection system that does roughly this." The former has a machine-checkable finish line; the latter requires human judgment at every step. The experiment measures the cheapest way to produce a conforming implementation given a complete specification — essentially the CI/CD-driven development case. That's useful, but it's not the general case of software development.

**The original development process can't be compared directly.** Sonnet + human iteration over multiple sessions produced both the implementation and the test contract simultaneously. None of the three runs replicate that process — they all benefit from hindsight encoded in the tests. A fairer comparison of "frontier vs orchestrated" for novel development would require both approaches to start from a vague brief and co-develop tests alongside implementation, which is a much harder experiment to control.

---

## Experimental Limitations

1. **Single project**: Results may not generalize. A larger or more complex project might shift the cost tradeoffs.

2. **Single worker model**: Only gpt-oss:20b-128k was used for successful completions. Other models (smaller or different architectures) might require more iteration, making the orchestration overhead more justified.

3. **Infrastructure issues**: ~5 min of B2's wall time was lost to host 180's GPU spilling to CPU. With proper parallel infrastructure, B2 could have been ~11 min.

4. **Same orchestrator as Run A**: Opus 4.6 served as both the direct implementer (Run A) and the orchestrator (B2). A weaker orchestrator (e.g., Sonnet) would test whether the planning/spec role actually requires frontier intelligence.

5. **Fixed test contract**: The acceptance tests were pre-written and stable. In a real project, requirements drift and test changes would add iteration costs to both approaches.

---

## Raw Data

All transcripts, specs, and worker outputs are preserved in:
- `results/run-a2-clean/` — A2 (isolated frontier baseline) transcript and summary
- `results/run-b-orchestrated/` — B1 transcript and summary
- `results/run-b2-strict/` — B2 transcript, summary, specs, and worker outputs
- `results/run-b3-nocode/` — B3 transcript, summary, specs, and worker outputs
