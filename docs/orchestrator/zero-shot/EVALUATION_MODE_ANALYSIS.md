# Evaluation Mode Analysis: Zero-Shot vs Iterative Feedback

## The Problem

**Current koderz behavior violates HumanEval zero-shot evaluation standards.**

We're showing assertion errors like:
```python
assert candidate([1.0, 2.0, 5.9, 4.0], 0.95) == True
```

This reveals:
- ✗ Exact test input values
- ✗ Expected output
- ✗ Effectively shows the test case

**HumanEval best practice:**
> "You should only feed the function signature and the docstring to the model.
> Do not include the unit tests in the prompt, as this would violate the
> zero-shot or few-shot nature of the evaluation."

---

## Two Distinct Modes

### Mode A: Standard HumanEval Evaluation (Zero-Shot)

**What it measures:**
- Model's ability to solve problems from specification alone
- Comparable to published benchmarks (GPT-4: 67%, Qwen2.5-Coder: 86.6%)
- Industry standard metric

**Protocol:**
```
1. Provide ONLY: function signature + docstring
2. Model generates solution (1 attempt or n samples for pass@k)
3. Run tests
4. Report: pass@1, pass@10, etc.
5. NO feedback to model about failures
```

**Pros:**
- ✅ Standardized, comparable results
- ✅ Tests model's true understanding
- ✅ Can publish benchmark scores
- ✅ Fair comparison to other systems

**Cons:**
- ❌ Single attempt - no learning
- ❌ Doesn't utilize iteration capability
- ❌ Lower success rate

---

### Mode B: Iterative Improvement with Feedback (Current)

**What it measures:**
- Model's ability to debug and refine solutions
- Effectiveness of error feedback and iteration
- Real-world development process (code → test → fix → repeat)

**Protocol:**
```
1. Provide: function signature + docstring + spec
2. Model generates solution
3. Run tests
4. If failed: provide error message
5. Model debugs and refines
6. Repeat until success or max iterations
```

**Pros:**
- ✅ Higher success rate through iteration
- ✅ Tests debugging capability
- ✅ More realistic development workflow
- ✅ Can measure "iterations to solve"

**Cons:**
- ❌ NOT comparable to HumanEval benchmarks
- ❌ Reveals test cases progressively
- ❌ Models can overfit to specific test inputs
- ❌ Results can't be published as "HumanEval pass@k"

---

## What Are We Actually Measuring?

### Current Koderz Architecture

**Phase 1: Spec Generation**
- Frontier model generates detailed specification
- Already provides more than "zero-shot" (spec is extra context)

**Phase 2: Iterative Execution**
- Local model implements based on spec
- Receives test failure feedback
- Iterates with error information
- Gets checkpoint guidance from frontier model

**This is NOT HumanEval pass@k evaluation!**

This is more like:
- **Agentic problem solving with feedback**
- **Multi-model collaborative debugging**
- **Iterative refinement workflow**

---

## Published Research Precedents

### Similar Iterative Approaches

1. **Self-Debugging (ICLR 2024)**
   - Models receive test failure feedback
   - Iterate to fix bugs
   - NOT reported as standard HumanEval pass@k

2. **T³ Method (June 2025)**
   - Dual-phase: diagnosis → repair
   - Uses error feedback for refinement
   - Reported separately from zero-shot metrics

3. **DR-CoT (2025)**
   - Dynamic recursive refinement
   - Multiple iterations with reflection
   - Different evaluation protocol

**Key pattern:** Research that uses feedback loops reports results under different metrics, not standard pass@k.

---

## Implications for Koderz

### Current Reality Check

**What we're calling it:**
- "Running on HumanEval"
- Measuring cost savings vs frontier-only

**What it actually is:**
- Multi-agent iterative problem solving
- Frontier spec generation + local implementation + frontier guidance
- Feedback-driven debugging

**Metrics we should report:**
- ✅ Success rate after N iterations
- ✅ Iterations to solution (avg, median)
- ✅ Cost per solved problem
- ✅ Savings vs frontier-only approach
- ❌ NOT "HumanEval pass@1" (that requires zero-shot)

---

## Options Forward

### Option 1: Add True Zero-Shot Mode

**Implementation:**
```python
def run_experiment(
    ...
    mode: str = "iterative"  # or "zero-shot"
):
    if mode == "zero-shot":
        # Single attempt, no error feedback
        result = local_model.generate(problem['prompt'])
        success = verify_solution(result)
        return {"success": success, "attempts": 1}

    else:  # iterative mode
        # Current behavior with feedback
        ...
```

**Benefits:**
- Can measure both standard HumanEval pass@k AND iterative success
- Compare local model's zero-shot vs with-feedback performance
- Publishable benchmark results

**Example results:**
```
Qwen2.5-Coder:32b on HumanEval/0:
  Zero-shot pass@1: 0% (failed on first attempt)
  Iterative (5 iter): 0% (still failed, but with good reasoning)
  Iterative (20 iter): Unknown (would need to test)

  With frontier guidance:
    Checkpoint @5: Provided contradictory advice
    Final result: Failed
```

---

### Option 2: Sanitize Error Messages

**Hide test inputs, show only error type:**

```python
# Current (reveals test case)
Error: assert candidate([1.0, 2.0, 5.9, 4.0], 0.95) == True
       AssertionError

# Sanitized (hides specific values)
Error: AssertionError in test case #3
       Expected: True
       Actual: False

# Or even more minimal:
Error: Failed 3 out of 5 test cases
       (No specific inputs or outputs shown)
```

**Pros:**
- ✅ Maintains some zero-shot integrity
- ✅ Still allows iteration
- ✅ Model must debug without seeing exact test inputs

**Cons:**
- ❌ Much harder to debug
- ❌ Models likely perform worse
- ❌ Still not truly zero-shot (knows it failed)

---

### Option 3: Embrace Iterative Mode, Report Honestly

**Accept that koderz is NOT standard HumanEval evaluation.**

**Clear documentation:**
```markdown
## Koderz Evaluation Protocol

Koderz does NOT use standard HumanEval pass@k evaluation. Instead, it measures:

- **Multi-agent collaborative problem solving**
- **Iterative refinement with test feedback**
- **Cost efficiency of frontier + local model swarm**

### Metrics:
- Success rate after N iterations (with feedback)
- Average iterations to solution
- Cost per solved problem
- Comparison to frontier-only baseline

### Important:
Results are NOT comparable to published HumanEval pass@1 scores, which
measure zero-shot performance without test feedback.
```

**Benefits:**
- ✅ Honest about what we're measuring
- ✅ Can focus on iteration effectiveness
- ✅ Cost analysis remains valid
- ✅ No false comparisons

**Example research questions:**
- How many iterations does local model need with feedback?
- Does frontier guidance actually help or hurt?
- What's the cost/benefit of iteration vs using frontier throughout?
- Can we achieve higher solve rate than frontier zero-shot?

---

## Recommendation

**Implement Option 1 + Option 3:**

### Short-term (Option 3):
1. **Document that koderz uses iterative evaluation**
   - NOT standard HumanEval pass@k
   - Feedback-driven debugging workflow
   - Multi-agent collaborative solving

2. **Report appropriate metrics:**
   ```
   Experiment Results:
   - Problem: HumanEval/0
   - Local model: Qwen2.5-Coder:32b
   - Mode: Iterative with test feedback
   - Max iterations: 20
   - Result: Failed after 20 iterations
   - Observations: Strong debugging reasoning, ambiguous test case
   - Cost: $0.04 vs $0.10 frontier-only (60% savings)
   ```

3. **Compare to baseline:**
   - Not to published pass@k scores
   - To "frontier-only iterative" approach
   - To "frontier-only zero-shot" approach

### Medium-term (Option 1):
4. **Add zero-shot evaluation mode:**
   ```python
   # Zero-shot: single attempt, no feedback
   koderz run --problem-id HumanEval/0 --mode zero-shot

   # Iterative: current behavior
   koderz run --problem-id HumanEval/0 --mode iterative --max-iterations 20
   ```

5. **Measure both:**
   - Zero-shot pass@1 (comparable to benchmarks)
   - Iterative success rate (research question)
   - Compare gains from iteration

---

## Comparison to Existing Research

### How other work handles this:

**Self-Debugging (ICLR 2024):**
- Clearly states it uses test feedback
- Reports "success after debugging" separately from pass@1
- Compares to pass@1 as baseline

**Reflexion (NeurIPS 2023):**
- Agent receives environment feedback
- Reports "solve rate with reflection" vs "without reflection"
- NOT reported as standard benchmark pass@k

**Program-of-Thought:**
- Delegates computation to interpreter
- Different evaluation protocol
- Comparable within PoT paradigm, not to zero-shot

**Our approach should be similar:**
- Report "solve rate with iterative feedback"
- Compare to "frontier-only with same iterations"
- Measure cost efficiency
- NOT claim standard HumanEval pass@k scores

---

## Proposed Changes

### 1. Update Documentation

**README.md:**
```markdown
## Evaluation Methodology

Koderz uses an **iterative, feedback-driven evaluation protocol** distinct
from standard HumanEval pass@k benchmarking:

1. Frontier model generates detailed specification
2. Local model implements solution
3. Tests executed, feedback provided
4. Model refines based on errors
5. Checkpoint guidance from frontier model
6. Repeat until success or max iterations

This measures:
- Multi-model collaborative problem solving
- Iterative debugging effectiveness
- Cost efficiency vs frontier-only baseline

**Note:** Results are not directly comparable to published HumanEval pass@k
scores, which use zero-shot evaluation without test feedback.
```

### 2. Add Zero-Shot Mode Flag

**orchestrator.py:**
```python
async def run_experiment(
    self,
    problem: dict,
    max_iterations: int = 50,
    mode: str = "iterative",  # NEW: "zero-shot" or "iterative"
    ...
):
    if mode == "zero-shot":
        # Single attempt, no error feedback
        return await self._run_zero_shot(problem, ...)
    else:
        # Current iterative behavior
        return await self._run_iterative(problem, max_iterations, ...)
```

### 3. Enhanced Metrics Reporting

**Output format:**
```
============================================================
Experiment Complete: exp_1c9bbb64
============================================================
Problem: HumanEval/0
Mode: Iterative with test feedback
Local Model: qwen2.5-coder:32b
Frontier Model: claude-sonnet-4-5

Results:
  Success: False
  Iterations: 5/5
  Solved at iteration: N/A

Cost Analysis:
  Total: $0.0427
  Frontier costs: $0.0427 (spec + checkpoint)
  Local costs: $0.0000 (5 iterations)

  Baseline comparison:
    Frontier-only (5 iter): ~$0.1069
    Savings: 60%

Observations:
  - Model demonstrated strong debugging reasoning
  - Correctly traced execution and identified inconsistency
  - Test case may be ambiguous (requires clarification)

Note: This is iterative evaluation with test feedback, not
      standard HumanEval pass@1 zero-shot evaluation.
============================================================
```

### 4. Separate Zero-Shot Baseline

**Run both modes for comparison:**
```bash
# Zero-shot (comparable to benchmarks)
koderz run --problem-id HumanEval/0 --mode zero-shot

# Iterative (current approach)
koderz run --problem-id HumanEval/0 --mode iterative --max-iterations 20
```

**Report delta:**
```
Zero-shot pass@1: 0/1 (0%)
Iterative success: 1/1 (100%, solved at iteration 7)
Improvement: +100% from iterative feedback
Average iterations to solve: 7
```

---

## Conclusion

**Key points:**

1. **Current koderz violates zero-shot evaluation** by showing test errors
   - Reveals test inputs and expected outputs
   - Not comparable to published HumanEval benchmarks

2. **This isn't necessarily wrong** - it's just a different evaluation mode
   - Iterative feedback-driven debugging
   - Multi-agent collaboration
   - Real-world development workflow

3. **We should be honest about what we're measuring:**
   - NOT: "HumanEval pass@1 with Qwen2.5-Coder"
   - YES: "Iterative problem solving with test feedback"
   - Metrics: iterations to solve, cost efficiency, success rate

4. **Add zero-shot mode for completeness:**
   - Can then measure both protocols
   - Compare zero-shot vs iterative
   - Publish legitimate benchmark numbers

5. **This doesn't invalidate koderz's value:**
   - Cost analysis still valid (comparing apples to apples)
   - Research questions about iteration still interesting
   - Real-world applicability (devs DO get test feedback)
   - Just need to report it correctly

**Action items:**
1. ✅ Document iterative evaluation protocol clearly
2. 🔧 Add zero-shot mode flag
3. 🔧 Update metrics reporting format
4. 🔧 Run experiments in both modes for comparison
