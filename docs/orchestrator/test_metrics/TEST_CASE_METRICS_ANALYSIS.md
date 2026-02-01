# Test Case Pass Rate as a Research Metric

## Research Question
**Should we track what percentage of test cases passed for each problem, even when the problem isn't fully solved?**

**Answer: YES - High research value as a secondary metric.**

---

## Why This Is Valuable

### 1. **Progress Measurement (Iteration Dynamics)**

**Current view (binary):**
```
Iteration 1: Failed
Iteration 2: Failed
Iteration 3: Failed
Iteration 4: Failed
Iteration 5: Success
```
→ Looks like no progress until sudden breakthrough

**With test pass rate:**
```
Iteration 1: 0/5 tests (0%)   - Import error
Iteration 2: 2/5 tests (40%)  - Fixed import, some logic works
Iteration 3: 3/5 tests (60%)  - Improved edge cases
Iteration 4: 4/5 tests (80%)  - Almost there
Iteration 5: 5/5 tests (100%) - Solved!
```
→ Shows steady incremental progress

**Research value:**
- Understand if models make gradual improvements or sudden breakthroughs
- Identify when models plateau (stuck at same test pass rate)
- Measure effectiveness of debugging prompts

---

### 2. **Failure Mode Analysis**

**Different types of failure:**

```
Problem A (Unsolved):
  Final: 1/10 tests (10%)
  → Fundamentally wrong approach

Problem B (Unsolved):
  Final: 9/10 tests (90%)
  → Close! Just missing edge case

Problem C (Unsolved):
  Final: 0/10 tests (0%)
  → Syntax error or completely misunderstood
```

**Research value:**
- Categorize failures: "completely wrong" vs "almost solved"
- Prioritize which problems to investigate
- Identify systematic weaknesses (e.g., edge cases vs core logic)

---

### 3. **Model Comparison (More Granular)**

**Current binary comparison:**
```
Model A: 100/164 problems solved (61%)
Model B: 100/164 problems solved (61%)
→ Appear equal
```

**With test pass rates:**
```
Model A:
  Solved: 100/164 (61%)
  Average test pass rate across ALL problems: 72%
  Average on unsolved: 40%

Model B:
  Solved: 100/164 (61%)
  Average test pass rate across ALL problems: 81%
  Average on unsolved: 65%
```
→ Model B is "closer" on unsolved problems

**Research value:**
- More nuanced model capabilities assessment
- Identify which model is "almost there" on more problems
- Guide model selection and improvement strategies

---

### 4. **Checkpoint Effectiveness**

**Measure if frontier guidance actually helps:**

```
Problem HumanEval/42:
  Iteration 1-5: 3/8 tests (37.5%)
  [Checkpoint guidance at iteration 5]
  Iteration 6: 6/8 tests (75%)
  Iteration 7: 8/8 tests (100%) - Solved!
```
→ Checkpoint caused jump from 37.5% → 75%

**Vs. ineffective guidance:**
```
Problem HumanEval/15:
  Iteration 1-5: 2/6 tests (33%)
  [Checkpoint guidance at iteration 5]
  Iteration 6-10: 2/6 tests (33%)
  → Guidance didn't help (plateau)
```

**Research value:**
- Quantify checkpoint guidance quality
- Identify when checkpoints are most helpful
- Optimize checkpoint timing (trigger on plateaus, not fixed intervals)

---

### 5. **Learning Curves & Plateau Detection**

**Identify stuck iterations:**
```
Iteration 1: 20%
Iteration 2: 40%
Iteration 3: 60%
Iteration 4: 60%
Iteration 5: 60%
Iteration 6: 60%
→ Plateaued at 60% - trigger checkpoint NOW
```

**Research value:**
- Dynamic checkpoint triggering (plateau-based, not fixed N)
- Early stopping when stuck
- Resource allocation (stop wasting iterations when stuck)

---

### 6. **Cost-Benefit Analysis**

**Marginal value of iterations:**
```
Iteration 1: 0% → 40% (+40% for $0.00 local)
Iteration 2: 40% → 70% (+30% for $0.00 local)
Iteration 3: 70% → 75% (+5% for $0.00 local)
[Checkpoint at iter 5]
Iteration 6: 75% → 95% (+20% for $0.02 frontier)
Iteration 7: 95% → 100% (+5% for $0.00 local)
```

**Research insights:**
- Early iterations (1-3) provide most value
- Late iterations have diminishing returns
- Checkpoints provide boost when needed

---

### 7. **Debugging Strategy Insights**

**Pattern analysis:**
```
Common pattern for logic errors:
  Iteration 1: 0% (import error)
  Iteration 2: 60% (basic cases work)
  Iteration 3-5: 60% (stuck on edge cases)
  → Need better edge case debugging prompts

Common pattern for syntax errors:
  Iteration 1: 0% (syntax error)
  Iteration 2: 100% (solved once syntax fixed)
  → Syntax errors are easy to fix
```

**Research value:**
- Identify which error types are hardest to debug
- Optimize debugging prompts for common patterns
- Understand model debugging capabilities

---

## Implementation Considerations

### Challenges

**1. Test Suite Structure Varies:**
```
HumanEval problems have different numbers of tests:
  Problem A: 3 tests  (each worth 33.3%)
  Problem B: 10 tests (each worth 10%)
  Problem C: 5 tests  (each worth 20%)
```
→ Passing "1 test" has different meaning

**2. Test Quality Varies:**
```
Test 1: assert func([]) == []           # Easy: empty input
Test 2: assert func([1,2,3]) == [1,2,3] # Easy: basic case
Test 3: assert func([1e308]) == [1e308] # Hard: edge case
```
→ Passing 2/3 tests might mean "got easy cases, missed edge case"

**3. Parsing Complexity:**
```python
# Current: Simple binary check
result = subprocess.run(...)
success = result.returncode == 0

# New: Need to parse assertions
# Count passed vs failed in output
# Handle different assertion formats
```

### Solutions

**1. Normalize by test count:**
```python
test_pass_rate = passed_tests / total_tests  # 0.0 to 1.0
```

**2. Track both raw and normalized:**
```python
metrics = {
    "tests_passed": 4,
    "tests_total": 5,
    "test_pass_rate": 0.80,  # 80%
    "binary_success": False  # Not all passed
}
```

**3. Use pytest or unittest for structured parsing:**
```python
# Run with pytest -v to get per-test results
# Parse output to count passed/failed
```

---

## Proposed Implementation

### Enhanced Test Execution

```python
def execute_with_test_breakdown(code: str, test: str) -> dict:
    """Execute solution and count individual test results."""

    # Run tests with verbose output
    result = subprocess.run(
        ["python3", "-m", "pytest", "-v", temp_file],
        capture_output=True,
        text=True,
        timeout=5
    )

    # Parse pytest output to count passed/failed
    passed = parse_passed_count(result.stdout)
    total = parse_total_count(result.stdout)

    return {
        "binary_success": result.returncode == 0,
        "tests_passed": passed,
        "tests_total": total,
        "test_pass_rate": passed / total if total > 0 else 0.0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "error": None if result.returncode == 0 else result.stderr
    }
```

### Enhanced Reporting

```python
# Per-iteration tracking
iteration_metrics = {
    "iteration": 3,
    "binary_success": False,
    "tests_passed": 4,
    "tests_total": 5,
    "test_pass_rate": 0.80,
    "improvement": 0.20  # vs previous iteration
}

# Aggregate across iterations
problem_metrics = {
    "problem_id": "HumanEval/0",
    "binary_success": True,
    "iterations_to_solve": 5,
    "test_progression": [0.0, 0.4, 0.6, 0.8, 1.0],
    "plateau_detected": False,
    "max_test_rate_reached": 1.0
}
```

### Output Format

```
Problem: HumanEval/42
Status: Unsolved after 20 iterations

Test Case Progression:
  Iteration  1: 0/8 tests (0.0%)   [+0.0%]
  Iteration  2: 3/8 tests (37.5%)  [+37.5%]
  Iteration  3: 3/8 tests (37.5%)  [+0.0%]
  Iteration  4: 5/8 tests (62.5%)  [+25.0%]
  Iteration  5: 5/8 tests (62.5%)  [+0.0%]
  [Checkpoint: Frontier guidance provided]
  Iteration  6: 7/8 tests (87.5%)  [+25.0%]
  Iteration  7: 7/8 tests (87.5%)  [+0.0%]
  ...
  Iteration 20: 7/8 tests (87.5%)  [+0.0%]

Analysis:
  Binary success: False (not fully solved)
  Peak test pass rate: 87.5% (7/8 tests)
  Plateau detected at iteration 7 (remained at 87.5%)
  Checkpoint at iteration 5 → improvement (+25%)
  Stuck test: Likely edge case issue (7/8 passing)

Research Value:
  - Model made significant progress (0% → 87.5%)
  - Checkpoint was effective (+25% improvement)
  - Final plateau suggests specific edge case confusion
  - "Almost solved" - high value for future investigation
```

---

## Research Questions Enabled

With test pass rate tracking, we can investigate:

1. **Iteration dynamics:**
   - Do models improve steadily or in jumps?
   - What's the typical improvement curve shape?
   - At what point do most models plateau?

2. **Checkpoint optimization:**
   - When are checkpoints most effective?
   - Should we trigger on plateaus vs fixed intervals?
   - What test pass rate predicts checkpoint benefit?

3. **Model capabilities:**
   - Which models get "close" more often?
   - Are some models better at edge cases vs core logic?
   - Test pass rate as proxy for partial understanding?

4. **Problem difficulty:**
   - Problems with high "almost solved" rates are harder
   - Correlate test pass rate with problem complexity
   - Identify which types of tests are hardest

5. **Debugging effectiveness:**
   - Does CoT prompting improve test pass rate progression?
   - Which debugging strategies yield fastest improvements?
   - Optimal prompt structure for different error types?

6. **Resource allocation:**
   - Stop early if stuck at low test pass rate
   - Continue if making steady progress
   - Dynamic max_iterations based on trajectory

---

## Recommended Approach

### Phase 1: Simple Implementation (Now)
```python
# Add basic test counting to current execution
def count_passed_tests(stderr: str) -> tuple[int, int]:
    """Parse assertion errors to count passed vs total tests."""
    # Count lines like: "assert candidate(...) == ..."
    # vs actual failures in traceback
    # Return (passed, total)
```

### Phase 2: Enhanced Parsing (Later)
```python
# Use pytest with structured output
# Get per-test granularity
# Track which specific tests fail
```

### Phase 3: Analysis Tools (Future)
```python
# Visualize test progression curves
# Cluster problems by difficulty (test pass rate distribution)
# Optimize checkpoint timing based on plateaus
```

---

## Conclusion

**Primary Metric: Binary Success**
- Standard HumanEval evaluation
- Comparable to published benchmarks
- Clear success/failure criteria

**Secondary Metric: Test Pass Rate**
- Research insights into model behavior
- Progress measurement during iteration
- Failure mode classification
- Checkpoint effectiveness evaluation
- More nuanced model comparison

**Recommendation:**
✅ **Track both metrics**
- Report binary success for standard comparison
- Use test pass rate for research analysis
- Both provide complementary insights

**Implementation priority:** Medium-High
- High research value
- Moderate implementation complexity
- Enables new research directions

**This would significantly enhance koderz's research value while maintaining standard benchmark compatibility.**
