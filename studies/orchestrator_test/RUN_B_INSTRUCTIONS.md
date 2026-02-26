# Run B: Orchestrated Implementation

You are the **orchestrator** for Run B of a koderz experiment. Your job is to
oversee implementation of an agentmon clone by delegating coding work to local 
models via planning, minimally-sufficient specs, and review guidance.

## Ground Rules

1. **You (Opus) do NOT write implementation code** unless escalating via
   the "take over" policy. All code must come from local worker models. Do NOT
   provide specs that contain actual Python code.
2. **You plan, spec, review, and guide.** Your output is subtask specs, interface
   contracts, corrective feedback, and integration glue.
3. **The acceptance tests are fixed.** See `tests/test_agentmon_acceptance.py` —
   neither you nor the workers may modify them. Target: 100/100 passing.
4. **Assessment criteria** include: all tests passing while minimizing token use by the
   orchestrator (Opus) -- the delegation burden should be primarily borne by the workers.
   Think like a human senior developer, only offer guidance when workers are failing,
   but don't provide full answers.
4. **Track every cost.** Log orchestrator tokens (your own) and worker tokens
   separately. Note escalation events.
5. **No reference implementation exists.** There is no prior implementation to
   read. You must derive all specs from the test contract and SPEC.md only.
   Do NOT look for or read any `agentmon_frontier/` or prior `agentmon/` directory.

## Available Resources

### Worker Models (all free, local Ollama)

| Host | Models | GPUs |
|------|--------|------|
| 192.168.1.74 | qwen3-coder:latest | 2x RTX 3090 |

Two GPUs are available, so favor running two worker tasks in parallel when possible.

### Subtask Orchestration Script (preferred)

`scripts/orchestrate_subtask.py` combines worker call + file extraction + file writing +
test running into a single command. The default worker model is **qwen3-coder:latest**.

**IMPORTANT: Always use `--diagnose` on every worker call.** This lets Haiku auto-fix
test failures without costing your (Opus) tokens. Haiku diagnostic calls cost ~$0.01 each.

```bash
# Standard call: worker + auto-diagnose on failure (USE THIS FOR ALL SUBTASKS)
python scripts/orchestrate_subtask.py \
    --spec specs/subtask1.md \
    --tests "tests/test_agentmon_acceptance.py::TestDataModels tests/test_agentmon_acceptance.py::TestEventStore" \
    --diagnose

# Manual fix with context (ONLY after --diagnose exhausts retries)
python scripts/orchestrate_subtask.py \
    --spec specs/subtask1_fix.md \
    --context agentmon/storage/db.py \
    --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
    --diagnose

# Re-run tests only (no worker call), e.g. after verifying a fix
python scripts/orchestrate_subtask.py \
    --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
    --test-only
```

Output is JSON to stdout (progress goes to stderr):
```json
{
  "files_written": ["agentmon/models/events.py", "agentmon/storage/db.py"],
  "worker_tokens": {"prompt": 1281, "completion": 6054},
  "worker_time_seconds": 48.8,
  "test_pattern": "tests/test_agentmon_acceptance.py::TestDataModels",
  "tests_passed": 7,
  "tests_failed": 0,
  "tests_error": 0,
  "test_output": "7 passed in 0.45s",
  "success": true,
  "retries": 1,
  "diagnostic_tokens": {"prompt": 2400, "completion": 200},
  "diagnostic_model": "claude-haiku-4-5-20251001",
  "iterations": [
    {"iter": 0, "tests_passed": 6, "tests_failed": 1},
    {"iter": 1, "tests_passed": 7, "tests_failed": 0}
  ]
}
```

The `retries`, `diagnostic_tokens`, `diagnostic_model`, and `iterations` fields only
appear when `--diagnose` is used.

**Important**: The worker's system prompt tells it to put a `# path/to/file.py` comment
as the first line of each fenced code block. The script uses this to know where to write
each file. qwen3-coder sometimes puts the path *before* the code fence — the extractor
handles both formats automatically. Specs should remind the worker of the expected file paths.

### Worker Script (low-level, for manual use)

```bash
# Send a prompt to a local model (without file writing or test running)
python scripts/ollama_worker.py \
    --model qwen3-coder:latest \
    --host http://192.168.1.74:11434 \
    --prompt-file subtask_spec.md \
    --json
```

### Project Structure

- `SPEC.md` — full project spec (test project = agentmon clone)
- `tests/test_agentmon_acceptance.py` — 100 acceptance tests (DO NOT MODIFY)
- `results/` — prior run cost/timing data (for reference only)

## Subtask Decomposition (from SPEC.md)

```
Subtask 1: Data models + storage layer (foundation, do first)
Subtask 2: Syslog receiver + parsers (depends on 1)
Subtask 3: Detection engine (depends on 1)
Subtask 4: LLM classifier + threat intel (depends on 1)
Subtask 5: CLI + alerting + configuration (depends on 1-4)
```

Parallelism plan: 1 → (2 + 3) → (4 + 5)

## Spec Writing Style (Arm B — Rich Logic)

qwen3-coder performs best with **rich logic specs** (Arm B style). Specs should include:
- Detailed structural guidance: module paths, class signatures, method names
- Rich behavioral descriptions: what each function does, edge cases, return types
- Interface contracts: what the module receives and returns
- Relevant test cases copied from the acceptance tests for context
- **No gotcha-style hints** — qwen3-coder handles standard patterns well without them
- **No actual Python code or pseudocode** — describe behavior, don't implement it
- Remind the worker to put `# agentmon/path/file.py` as the first line in each code block

## Workflow Per Subtask

1. **Write a spec file** (e.g. `specs/subtask1.md`) using Arm B style (see above).

2. **Call orchestrate_subtask.py — always with `--diagnose`:**
   ```bash
   python scripts/orchestrate_subtask.py \
       --spec specs/subtask1.md \
       --tests "tests/test_agentmon_acceptance.py::TestDataModels tests/test_agentmon_acceptance.py::TestEventStore" \
       --diagnose
   ```

   The `--diagnose` flag is **mandatory on every call**. It handles the full
   initial-attempt + diagnosis + fix loop automatically:
   - On test failure, Haiku analyzes the spec + test output + current files
   - Haiku produces a short, targeted fix spec (typically 10-20 lines)
   - The worker is called again with the fix spec + current files as context
   - Tests re-run. Repeats up to `--max-retries` times (default: 2).

   **Do NOT call orchestrate_subtask.py without `--diagnose`.** Without it, you'll
   spend your own (expensive) tokens diagnosing failures that Haiku can handle for ~$0.01.

3. **Check the JSON result** — if `"success": true`, move to the next subtask.
   The `iterations` array shows the progression (e.g., 14/18 → 18/18).

4. **If `--diagnose` didn't fix it** (all retries exhausted), escalate:
   - Review the `test_output` and `iterations` in the JSON result
   - Write a short fix spec describing what went wrong and what to change
   - Call again with `--context` and `--diagnose` (so Haiku can still help on the retry):
     ```bash
     python scripts/orchestrate_subtask.py \
         --spec specs/subtask1_fix.md \
         --context agentmon/storage/db.py \
         --tests "tests/test_agentmon_acceptance.py::TestDataModels" \
         --diagnose
     ```

   **Do NOT paste file contents into specs.** The `--context` flag handles that.
   **Do NOT read the worker's files yourself.** That costs your tokens for no reason.

5. **Escalation ladder** (if stuck after diagnose + manual fix):
   - Level 1: **Re-spec** — rewrite the prompt with more detail/examples
   - Level 2: **Decompose** — break the subtask into smaller pieces
   - Level 3: **Take over** — you implement it directly (log this!)

## Measurement

Track and report at the end:
- Wall-clock time (captured by cost tracking wrapper)
- Orchestrator cost (your API cost, from status bar)
- Worker tokens per subtask (from orchestrate_subtask.py JSON output)
- Test pass rate (must reach 100/100)
- Escalation events (re-spec, decompose, take over) with trigger and outcome
- Fraction of code written by escalation vs workers

## Run A Baseline (to beat)

| Metric | Value |
|--------|-------|
| Wall clock | 6m 30s |
| API cost | $2.13 |
| Test pass rate | 100/100 |
