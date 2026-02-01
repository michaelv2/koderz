# Code Changes: Progressive Spec Disclosure System

**Date**: 2026-01-31
**Summary**: Implemented minimal initial specs + adaptive progressive disclosure at checkpoints

---

## ✅ All Code Changes Complete

### 1. Model Clients - Minimal Spec Generation (3 files)

**`koderz/models/frontier.py`** (lines 37-48)
- Changed prompt from "Generate a detailed..." to "Generate a MINIMAL..."
- Removed: implementation approach, test criteria, edge cases, common pitfalls, reference code
- Added: CRITICAL section explicitly forbidding algorithm hints and code skeletons

**`koderz/models/openai_client.py`** (lines 35-46)
- Same changes as frontier.py
- Ensures OpenAI and Anthropic models use identical minimal spec prompt

**`koderz/models/local.py`** (lines 134-165)
- **Bug fix**: Was not formatting prompt at all (just passing raw problem text)
- Now properly wraps problem in minimal spec prompt
- Ensures local models (Ollama) get same prompt as API models

### 2. Model Clients - Progressive Checkpoint Disclosure (2 files)

**`koderz/models/frontier.py`** (lines 67-255)
- Added `checkpoint_num` and `problem_prompt` parameters to `checkpoint_review()`
- Checkpoint 1: Generates strategic guidance (approach, edge cases, pitfalls) based on failures
- Checkpoint 2: Generates test criteria based on failure patterns
- Checkpoint 3+: Only debugging analysis (no new spec sections)
- Adaptive: Analyzes actual failures to generate targeted guidance

**`koderz/models/openai_client.py`** (lines 65-193)
- Same progressive disclosure logic as frontier.py
- Ensures OpenAI models (gpt-4o-mini, gpt-4o) work identically to Anthropic models

### 3. Orchestrator - Pass Checkpoint Context (1 file)

**`koderz/orchestrator.py`** (3 locations)
- Line 699-713: Updated `_checkpoint()` signature to accept `problem_prompt`
- Line 765-769: Pass `checkpoint_num` and `problem_prompt` to `checkpoint_review()`
- Line 380-387: Pass `problem["prompt"]` when calling `_checkpoint()`

### 4. Test Files - Updated Spec Prompts (4 files)

**`tests/test_spec_qwen_vs_gptoss.py`** (lines 23-36)
**`tests/test_spec_comparison.py`** (lines 25-38)
**`tests/test_spec_validation_gptoss.py`** (lines 38-51)
**`tests/test_spec_comparison_3way.py`** (lines 30-43)

All updated `create_spec_prompt()` function to use minimal prompt for consistency

---

## Files Modified Summary

**Total**: 10 files

**Core system** (4 files):
- koderz/models/frontier.py
- koderz/models/openai_client.py
- koderz/models/local.py
- koderz/orchestrator.py

**Test files** (4 files):
- tests/test_spec_qwen_vs_gptoss.py
- tests/test_spec_comparison.py
- tests/test_spec_validation_gptoss.py
- tests/test_spec_comparison_3way.py

**Documentation** (2 files):
- docs/orchestrator/PROGRESSIVE_SPEC_DISCLOSURE.md (new)
- test_results/progressive_spec_example_humaneval100.md (new)

---

## Verification

```bash
# No files with old detailed prompt
grep -l "Generate a detailed implementation specification" tests/*.py koderz/models/*.py
# Result: (none found) ✓

# 7 files with new minimal prompt
grep -l "Your spec should include ONLY:" tests/*.py koderz/models/*.py
# Result: 7 files ✓
```

---

## What Changed

### Before (Detailed Spec)
**Initial spec**: ~7,300 chars
- Problem analysis ✓
- Implementation approach (algorithm hints) ❌
- Test criteria (specific tests) ❌
- Edge cases (comprehensive list) ❌
- Common pitfalls ❌
- **Reference implementation skeleton** ❌

**Result**: Local model just copies provided solution

### After (Minimal Spec + Progressive Disclosure)

**Phase 1 - Initial spec**: ~700 chars (90% reduction)
- Problem analysis ✓
- Implementation specification ✓
- **Nothing else** ✓

**Checkpoint 1** (iteration 5): Adds strategic guidance
- Debugging analysis (4 sections)
- + Implementation approach (adaptive to failures)
- + Edge cases (causing current failures)
- + Common pitfalls (evident in attempts)

**Checkpoint 2** (iteration 10): Adds test criteria
- Debugging analysis (4 sections)
- + Test cases (targeting failure patterns)
- + Expected behavior (missing cases)

**Result**: Local model must actually solve the problem

---

## Impact on Benchmarks

### Minimal Spec Impact
- ✅ **90% shorter** generation (7,300 → 700 chars)
- ✅ **57% faster** generation (41s → 18s)
- ✅ **No algorithm hints** (tests actual coding ability)
- ⚠️ **Lower one-shot success** expected (was artificially inflated)

### Progressive Disclosure Impact
- ✅ **Adaptive guidance** based on actual failures
- ✅ **Senior/junior dynamic** (escalates as needed)
- ⚠️ **Higher cost** if many checkpoints needed (~10x vs direct solve)
- ⚠️ **Need to validate** if checkpoint overhead is worth it

---

## Next Steps

1. **Benchmark with new system**
   - Run subset of HumanEval (10-20 problems)
   - Measure: one-shot rate, avg iterations, checkpoint effectiveness
   - Compare: local+checkpoints vs direct frontier solve

2. **Cost analysis**
   - Track: % solved without checkpoints (zero cost)
   - Track: avg cost per problem (including checkpoint overhead)
   - Decision: Is adaptive escalation cheaper than direct solve?

3. **Iterate on design**
   - Adjust checkpoint_interval if needed (currently 5)
   - Tune progressive spec verbosity
   - Consider when to give up and use frontier directly

---

## Philosophy Reminder

**Senior/Junior Developer Relationship**
- Junior (local): Tries independently with minimal guidance
- Senior (frontier): Intervenes only when stuck
- Progressive disclosure: Just enough to unblock, not full solution
- Cost-aware: Only justified if most problems solve locally

**Adaptive Escalation**
- Start minimal (cheapest path)
- Escalate adaptively (based on failures)
- Question assumptions (is checkpoint overhead worth it?)
