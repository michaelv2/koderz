# Checkpoint Guidance Upgrade - Systematic & Test-Aware

## Summary

Enhanced frontier model checkpoint guidance to be **systematic** and **test-aware**, replacing generic advice with structured, actionable analysis.

**Implementation:** Option A (Systematic + Test-Aware)

---

## What Changed

### Before (Generic Guidance)

```
You are reviewing recent attempts by a local coding model...

1. Error Pattern Analysis: What is the consistent mistake?
2. Root Cause: What is the model missing?
3. Concrete Fix: Provide specific instructions

Format as:
**Analysis:** [Your analysis]
**Guidance:** [Instructions]
```

**Issues:**
- ❌ No test metrics visibility
- ❌ Generic prompts allow vague guidance
- ❌ No plateau detection
- ❌ Binary success/failure only
- ❌ No requirement for step-by-step analysis

**Example output:**
```
**Analysis:** The model is using the wrong comparison operator.

**Guidance:** Use <= instead of < in your comparison.
```

### After (Systematic & Test-Aware)

```
You must provide a SYSTEMATIC ANALYSIS following this exact structure:

## 1. FAILING TEST ANALYSIS
- Current test pass rate and what it tells us
- Specific input causing failure
- Expected vs actual output
- Which assertion failed

## 2. ROOT CAUSE DIAGNOSIS
- Step-by-step trace with failing input
- Variable values at each step
- Exact line where behavior diverges
- WHY this line causes failure

## 3. PROPOSED FIX
- Exact line(s) to change
- Corrected code
- WHY this fixes the root cause
- If plateau: suggest creative alternative

## 4. EDGE CASES TO VERIFY
- Other test cases that might fail
- Boundary conditions to handle
```

**Improvements:**
- ✅ Test pass rate visible (5/7 tests = 71%)
- ✅ Structured format enforces specificity
- ✅ Plateau detection built-in
- ✅ Requires step-by-step execution trace
- ✅ Must explain WHY fixes work

**Example output:**
```
## 1. FAILING TEST ANALYSIS
Test pass rate: 5/7 (71.4%)
This indicates the logic is mostly correct but fails on edge cases.

Based on the error traceback, test case 6 is failing with input:
- numbers = [1.0, 1.1]
- threshold = 0.1

Expected: True (because |1.0 - 1.1| = 0.1 equals threshold)
Actual: False

## 2. ROOT CAUSE DIAGNOSIS
Tracing execution with numbers=[1.0, 1.1], threshold=0.1:

Line 2: for i in range(len([1.0, 1.1])) → i = 0
Line 3: for j in range(1, 2) → j = 1
Line 4: abs(1.0 - 1.1) = 0.1
Line 4: Check if 0.1 < 0.1 → FALSE

The issue is on line 4: using `<` (strictly less than) when the problem
requires `<=` (less than or equal). When the distance exactly equals
the threshold, it should return True.

## 3. PROPOSED FIX
Change line 4 from:
```python
if abs(numbers[i] - numbers[j]) < threshold:
```

To:
```python
if abs(numbers[i] - numbers[j]) <= threshold:
```

This fixes the issue because "closer than threshold" in the problem
statement means distance ≤ threshold, not distance < threshold.

## 4. EDGE CASES TO VERIFY
After this fix, verify these cases:
- numbers=[1.0, 1.0], threshold=0.0 → True (exact match)
- Empty list → False (no pairs to compare)
- Single element → False (need at least 2 elements)
```

---

## Key Features

### 1. Test Metrics Visibility

**Iteration formatting now includes:**
```
### Iteration 3
**Code:**
```python
[code]
```

**Result:** ✗ FAILED - 5/7 tests passed (71.4%)
**Error:** AssertionError
```

**Benefits:**
- Frontier can see progress: 0% → 29% → 71%
- Can gauge how close to solution (0% = completely wrong, 70%+ = almost there)
- Distinguishes syntax errors (0% pass rate) from logic errors (partial pass rate)

---

### 2. Plateau Detection

**Automatic detection when stuck:**
```python
# If last 3 iterations have same pass rate (and it's not 0% or 100%)
⚠️ PLATEAU DETECTED: Model stuck at 71.4% pass rate for 3 consecutive iterations.
```

**Frontier model's response:**
- Recognizes current approach isn't working
- Suggests creative alternative algorithms
- Prevents infinite loops of identical guidance

**Example:**
```
## 3. PROPOSED FIX
⚠️ PLATEAU DETECTED - The current approach may be fundamentally wrong.

Instead of fixing the comparison operator, consider that the problem might
require a completely different algorithm. Try using a hash set approach:
[alternative solution]
```

---

### 3. Structured Format Enforcement

**4 required sections ensure:**

| Section | Purpose | Prevents |
|---------|---------|----------|
| **1. Failing Test Analysis** | Identify exact failing case | Vague "tests are failing" |
| **2. Root Cause Diagnosis** | Trace execution step-by-step | "The logic is wrong" |
| **3. Proposed Fix** | Specific code change + explanation | "Use <= instead of <" without context |
| **4. Edge Cases** | Think beyond immediate fix | Missing boundary conditions |

**Cannot provide:**
- ❌ "Check your comparison logic" (too vague)
- ❌ "Fix the operator" (doesn't explain why)
- ❌ "The code is wrong" (doesn't identify which line)

**Must provide:**
- ✅ Exact input that fails
- ✅ Step-by-step trace showing bug
- ✅ Specific line to change
- ✅ Explanation of why fix works

---

### 4. Progress Context

**Test pass rate progression shown:**
```
Iteration 1: 0/7 tests (0.0%)   - NameError: List not defined
Iteration 2: 2/7 tests (28.6%)  - AssertionError (logic error)
Iteration 3: 5/7 tests (71.4%)  - AssertionError (edge case)
Iteration 4: 5/7 tests (71.4%)  - AssertionError (same edge case)
Iteration 5: 5/7 tests (71.4%)  - PLATEAU DETECTED
```

**Frontier can see:**
- ✓ Import fixed between iter 1→2
- ✓ Logic partially fixed between iter 2→3
- ✗ Stuck at same edge case for 3 iterations → Need different approach

---

## Real-World Example: exp_a68727f3

### What Old Guidance Produced

**Checkpoint 1:**
```
**Analysis:** The comparison operator is incorrect.
**Guidance:** Use <= instead of <
```

**Checkpoint 2:**
```
**Analysis:** Still using wrong operator.
**Guidance:** Try >= instead
```

**Checkpoint 3:**
```
**Analysis:** The threshold check is backwards.
**Guidance:** Actually use < not <=
```

**Issues:**
- Contradictory (<=, >=, <)
- No explanation of WHY
- No step-by-step trace
- Local model confused

---

### What New Guidance Would Produce

**Checkpoint 1:**
```
## 1. FAILING TEST ANALYSIS
Test pass rate: 5/7 (71.4%)

The model is very close to solving this. Based on the error traceback,
test case 6 fails with:
- Input: numbers=[1.0, 1.1], threshold=0.1
- Expected: True
- Actual: False

This is an edge case where the distance exactly equals the threshold.

## 2. ROOT CAUSE DIAGNOSIS
Let's trace through the code with this failing input:

numbers=[1.0, 1.1], threshold=0.1

Line 2: for i in range(2):  # i will be 0, then 1
Line 3:   for j in range(i+1, 2):  # When i=0, j will be 1
Line 4:     Check: abs(numbers[0] - numbers[1]) < threshold
            = abs(1.0 - 1.1) < 0.1
            = 0.1 < 0.1
            = FALSE  ❌

The problem says "two numbers are closer than the given threshold"
which should include the case where distance equals the threshold.

The bug is on line 4: using strict inequality `<` when we need `<=`.

## 3. PROPOSED FIX
Change line 4 from:
```python
if abs(numbers[i] - numbers[j]) < threshold:
```

To:
```python
if abs(numbers[i] - numbers[j]) <= threshold:
```

Why this works:
- "Closer than threshold" means distance ≤ threshold
- The problem wants us to return True when distance equals threshold
- Using <= captures both strictly less than AND equal cases

## 4. EDGE CASES TO VERIFY
After making this change, the code should handle:
1. Exact match: numbers=[1.0, 1.0], threshold=0.0 → True
2. Just under threshold: numbers=[1.0, 1.09], threshold=0.1 → True
3. Exactly at threshold: numbers=[1.0, 1.1], threshold=0.1 → True ✓
4. Just over threshold: numbers=[1.0, 1.11], threshold=0.1 → False
5. Empty list: numbers=[], threshold=1.0 → False
```

**Benefits:**
- ✅ Clear identification of failing test
- ✅ Step-by-step trace showing exact bug
- ✅ Explains WHY <= not <
- ✅ Lists edge cases to verify
- ✅ Consistent, unambiguous guidance

---

## Implementation Details

### Modified Files

**1. `koderz/models/frontier.py`**
- Updated `checkpoint_review()` method
- Added test metrics to iteration formatting
- Implemented plateau detection (3+ iterations at same pass rate)
- Replaced generic prompt with 4-section structured format
- Increased max_tokens to 3072 for detailed analysis

**2. `koderz/models/openai_client.py`**
- Same updates as frontier.py for consistency
- Works with gpt-4o and gpt-4o-mini models

### Plateau Detection Logic

```python
# Check if last 3 rates are identical and not 0.0 or 1.0
if len(pass_rates) >= 3:
    last_three = pass_rates[-3:]
    if len(set(last_three)) == 1 and 0.0 < last_three[0] < 1.0:
        plateau_detected = True
        plateau_info = f"⚠️ PLATEAU DETECTED: Model stuck at {last_three[0]:.1%}"
```

**Why not 0.0 or 1.0:**
- 0.0 = syntax/import errors, expected to stay at 0% initially
- 1.0 = solved, no plateau issue
- Between 0-100% = logic/edge case issues, can get stuck

### Iteration Format

```python
def format_iteration(i, iter_data):
    metadata = iter_data.get('metadata', {})
    tests_passed = metadata.get('tests_passed', 0)
    tests_total = metadata.get('tests_total', 0)
    test_pass_rate = metadata.get('test_pass_rate', 0.0)

    if success:
        text = f"✓ PASSED all {tests_total} tests (100%)"
    else:
        text = f"✗ FAILED - {tests_passed}/{tests_total} tests passed ({test_pass_rate:.1%})"

    return text, test_pass_rate
```

---

## Research Value

### 1. Measure Guidance Quality

Can now quantitatively measure if guidance helps:

```python
# Before checkpoint
test_pass_rate = 0.714  # 5/7 tests

# After checkpoint
test_pass_rate = 1.0    # 7/7 tests

# Guidance effectiveness: +28.6%
```

### 2. Compare Guidance Strategies

Track which section of guidance helps most:
- Does step-by-step trace help more than code diff?
- Do edge case suggestions prevent regressions?
- Does plateau detection trigger better solutions?

### 3. Identify Common Failure Patterns

Analyze checkpoints to find:
- What % of plateaus are operator issues (< vs <=)?
- What % need algorithmic rethinking?
- Which error types benefit most from checkpoints?

### 4. Optimize Checkpoint Timing

```python
# Early plateau (iterations 2-4): Simple fix
# Late plateau (iterations 8-10): Fundamental issue

# Can we detect type of plateau and adjust guidance?
```

### 5. Model Comparison

Compare frontier models on guidance quality:
- Does Opus provide better root cause diagnosis than Sonnet?
- Which model gives most actionable fixes?
- Correlation between guidance cost and effectiveness?

---

## Validation

**Test:** `test_checkpoint_guidance.py`

```
✓ Test metrics correctly included in iteration formatting
✓ Plateau detected: 71.4% for 3 iterations
✓ Plateau detection working correctly
✓ Structured prompt format defined with 4 required sections

✅ All checkpoint guidance tests passed!
```

---

## Usage

**No changes needed!**

Checkpoint guidance automatically uses new format:

```bash
# Run experiment with checkpoints every 5 iterations
poetry run koderz run --problem-id "HumanEval/0" --mode iterative

# Checkpoints will automatically:
# 1. Show test pass rates
# 2. Detect plateaus
# 3. Provide structured guidance
# 4. Save detailed analysis to debug files
```

**Debug files include:**
```
exp_abc123_checkpoint01_guidance.txt
  - Full 4-section analysis
  - Test metrics
  - Plateau warnings (if applicable)
```

---

## Cost Impact

**Token usage:**
- Before: ~1,500 tokens (generic prompt + generic response)
- After: ~2,500 tokens (structured prompt + detailed analysis)
- Increase: ~67% per checkpoint

**Value:**
- More actionable guidance → fewer total iterations
- Better problem diagnosis → faster solve times
- Plateau detection → prevents wasted iterations

**Net impact:** Likely cost-neutral or cost-saving despite higher per-checkpoint cost.

---

## Future Enhancements

### 1. Parse Failing Test Input

Currently: Infer from error message
Future: Parse test code to extract exact failing input

```python
# From test code:
assert candidate([1.0, 1.1], 0.1) == True

# Extract:
failing_input = {"numbers": [1.0, 1.1], "threshold": 0.1}
expected = True
```

### 2. Dynamic Checkpoint Intervals

```python
# If plateau detected at iteration 5
# Trigger immediate checkpoint instead of waiting until iteration 10
```

### 3. Multi-Hypothesis Guidance

```python
## 3. PROPOSED FIX

HYPOTHESIS 1 (80% confidence): Operator issue
[detailed fix]

HYPOTHESIS 2 (15% confidence): Edge case handling
[alternative fix]

Try Hypothesis 1 first.
```

### 4. Guidance History Awareness

```python
# If checkpoint N > 1, show previous guidance
PREVIOUS GUIDANCE (Checkpoint 1):
"Use <= instead of <"

RESULT: Still failing at 71.4%

ANALYSIS: Previous guidance was correct but incomplete...
```

---

## Conclusion

**Implemented:** Systematic + Test-Aware checkpoint guidance (Option A)

**Key improvements:**
- ✅ Test metrics visible to frontier model
- ✅ Plateau detection prevents infinite loops
- ✅ Structured format enforces specificity
- ✅ Step-by-step traces required
- ✅ Explanations of WHY fixes work

**Research value:**
- Quantifiable guidance effectiveness
- Ability to compare frontier models
- Pattern analysis across checkpoints
- Optimization opportunities

**Next steps:**
- Run experiments to gather checkpoint guidance data
- Analyze effectiveness vs old approach
- Consider implementing future enhancements
