# Checkpoint Guidance - Quick Reference

## What You Get Now

Frontier model checkpoints now provide **systematic, test-aware guidance** instead of generic advice.

---

## The 4-Section Format

Every checkpoint provides:

```
## 1. FAILING TEST ANALYSIS
- Test pass rate: 5/7 (71%)
- Failing input: [1.0, 1.1], threshold=0.1
- Expected: True, Actual: False

## 2. ROOT CAUSE DIAGNOSIS
Step-by-step trace:
- Line 4: abs(1.0 - 1.1) = 0.1
- Line 4: Check 0.1 < 0.1 → FALSE ❌
- Bug: Using < instead of <=

## 3. PROPOSED FIX
Change line 4 from:
  if abs(numbers[i] - numbers[j]) < threshold:
To:
  if abs(numbers[i] - numbers[j]) <= threshold:

Why: "Closer than" includes equal distance

## 4. EDGE CASES TO VERIFY
- Exact match: [1.0, 1.0], threshold=0.0
- Empty list should return False
- Single element should return False
```

---

## Test Metrics in Checkpoints

```
Iteration 1: ✗ FAILED - 0/7 tests (0%)   - Import error
Iteration 2: ✗ FAILED - 2/7 tests (29%)  - Logic error
Iteration 3: ✗ FAILED - 5/7 tests (71%)  - Edge case
Iteration 4: ✗ FAILED - 5/7 tests (71%)  - Same edge case
Iteration 5: ✗ FAILED - 5/7 tests (71%)  - PLATEAU!
```

**Frontier model can see:**
- Progress over iterations (0% → 29% → 71%)
- When model is stuck (plateau at 71%)
- How close to solving (71% = almost there)

---

## Plateau Detection

**Automatic warning when stuck:**
```
⚠️ PLATEAU DETECTED: Model stuck at 71.4% pass rate
   for 3 consecutive iterations.
```

**Frontier model response:**
- Suggests creative alternative approaches
- Avoids repeating same advice
- Indicates fundamental issue with current algorithm

---

## Before vs After

### Before (Generic)
```
**Analysis:** The comparison operator is wrong.

**Guidance:** Use <= instead of <
```

❌ No test metrics
❌ No explanation WHY
❌ No step-by-step trace
❌ Vague, potentially contradictory

### After (Systematic)
```
## 1. FAILING TEST ANALYSIS
Test 6/7 fails: numbers=[1.0, 1.1], threshold=0.1
Expected True, got False (71% pass rate)

## 2. ROOT CAUSE DIAGNOSIS
Trace with failing input:
- abs(1.0 - 1.1) = 0.1
- Check: 0.1 < 0.1 → FALSE
- Should be: 0.1 <= 0.1 → TRUE

## 3. PROPOSED FIX
Line 4: Change `<` to `<=`
Reason: Distance equal to threshold should return True

## 4. EDGE CASES
Verify: exact matches, empty lists, single elements
```

✅ Shows test pass rate
✅ Explains WHY fix works
✅ Step-by-step execution trace
✅ Specific, actionable, consistent

---

## Usage

**No changes required!**

```bash
poetry run koderz run --problem-id "HumanEval/0" --mode iterative
```

Checkpoints automatically include:
- Test pass rates
- Plateau detection
- Structured 4-section guidance
- Detailed execution traces

---

## Debug Files

Checkpoint guidance saved to:
```
debug_output/exp_abc123_checkpoint01_guidance.txt
```

Contains:
- Full 4-section analysis
- Test metrics for each iteration
- Plateau warnings (if detected)
- Complete frontier model reasoning

---

## Research Value

### What You Can Now Measure

**1. Guidance Effectiveness**
```
Before checkpoint: 71% pass rate
After checkpoint:  100% pass rate
Guidance impact:   +29%
```

**2. Failure Patterns**
- Syntax errors: Usually 0% → fast fix
- Logic errors: Gradual improvement
- Edge cases: Plateau at 70-90%

**3. Plateau Analysis**
- How often do plateaus occur?
- What triggers them? (operator bugs, algorithmic issues)
- Does plateau detection improve solve rate?

**4. Model Comparison**
- Which frontier model gives better guidance?
- Does Opus outperform Sonnet on complex bugs?
- Cost vs quality trade-offs

---

## Quick Examples

### Example 1: Operator Bug (Quick Fix)
```
Iteration 3: 5/7 tests (71%)
Checkpoint detects: < vs <= operator issue
Next iteration: 7/7 tests (100%) ✓
```

### Example 2: Plateau (Need Alternative)
```
Iteration 3-5: 4/7 tests (57%) - stuck
Checkpoint detects plateau
Suggests alternative algorithm
Iteration 6: 7/7 tests (100%) ✓
```

### Example 3: Syntax Error (No Plateau)
```
Iteration 1: 0/7 tests (0%) - Import error
Checkpoint: "Add: from typing import List"
Iteration 2: 7/7 tests (100%) ✓
```

---

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **Test Pass Rate** | See progress, not just fail/success |
| **Plateau Detection** | Prevent infinite loops |
| **Structured Format** | Consistent, specific guidance |
| **Step-by-Step Trace** | Understand exact bug location |
| **Edge Case Analysis** | Prevent regressions |
| **WHY Explanations** | Build better solutions |

---

## Comparison to Old Approach

| Aspect | Before | After |
|--------|--------|-------|
| Test visibility | Binary only | N/M tests (X%) |
| Progress tracking | None | See 0%→71%→100% |
| Plateau detection | None | Automatic warning |
| Specificity | Often vague | 4 required sections |
| Execution trace | Optional | Required |
| Explanations | Sometimes | Always (WHY fixes work) |
| Consistency | Variable | Enforced structure |

---

## Tips for Best Results

1. **Enable debug mode** to save checkpoint guidance files
2. **Review checkpoint files** after experiments to see frontier reasoning
3. **Track effectiveness** by comparing pass rates before/after checkpoints
4. **Adjust checkpoint interval** if needed (default: every 5 iterations)

---

## Summary

**Old approach:** Generic advice that might help
**New approach:** Systematic analysis that should help

**Key improvement:** Frontier model now **sees test metrics** and **must provide structured guidance** with step-by-step traces and specific fixes.

**Result:** More actionable, consistent, and effective checkpoint guidance.
