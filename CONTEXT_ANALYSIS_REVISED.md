# Revised Context Window Analysis

## User's Correction

**Original claim (WRONG):** Context accumulates across all iterations, needing 8K+

**Reality (CORRECT):** Each iteration is a separate API call. Context doesn't accumulate across calls.

## Actual Context Usage Per Call

Based on `orchestrator.py` inspection:

### Spec Generation Call
```
Problem description + instructions:    ~800 tokens
Spec output (gpt-oss:20b avg):      ~1,650 tokens
---------------------------------------------------
Total:                               ~2,450 tokens
```
**Minimum needed:** 3K context ✅ 4K sufficient

### Iteration 1 (First Attempt)
```
System prompt:                         ~250 tokens
Spec:                                ~1,650 tokens
Problem:                               ~500 tokens
Output (code):                         ~800 tokens
---------------------------------------------------
Total:                               ~3,200 tokens
```
**Minimum needed:** 4K context ✅ 4K sufficient (tight)

### Iterations 2+ (With Error Feedback)
```
System prompt:                         ~250 tokens
Spec:                                ~1,650 tokens
Problem:                               ~500 tokens
Previous error:                        ~300 tokens
Previous code:                         ~300 tokens
Debug instructions:                    ~200 tokens
Output (code):                         ~800 tokens
---------------------------------------------------
Total:                               ~4,000 tokens
```
**Minimum needed:** 4K context ⚠️ 4K barely sufficient, 6K safer

### Checkpoint Iterations (Every 5th)
```
System prompt:                         ~250 tokens
Spec:                                ~1,650 tokens
Problem:                               ~500 tokens
Previous error:                        ~300 tokens
Previous code:                         ~300 tokens
Checkpoint guidance:                 ~2,000 tokens
Output (code):                         ~800 tokens
---------------------------------------------------
Total:                               ~5,800 tokens
```
**Minimum needed:** 6K context ❌ 4K insufficient, 8K needed

## Conclusion

**You're right** that 8K is overkill for regular iterations, but:

1. **Checkpoint iterations** (every 5th) can hit ~5,800 tokens
2. **4K is too tight** for iterations 2+ with error feedback (~4,000 tokens)
3. **8K provides headroom** for longer error messages or guidance

## Optimal Strategy

### Option 1: Static 8K (Current Implementation)
**Pro:** Simple, handles all cases
**Con:** Wastes memory on non-checkpoint iterations

### Option 2: Dynamic Context Sizing
Adjust `num_ctx` based on what's being included:

```python
def calculate_num_ctx(
    has_checkpoint_guidance: bool,
    iteration: int
) -> int:
    if has_checkpoint_guidance:
        return 8192  # Checkpoint iterations
    elif iteration > 1:
        return 6144  # Error feedback iterations
    else:
        return 4096  # First iteration
```

### Option 3: Reduce 8K → 6K Default
6K handles checkpoint iterations with safety margin:
- Most iterations: 3-4K (plenty of headroom)
- Checkpoint iterations: 5.8K (safe)
- Memory savings: 25% vs 8K

## Recommendation

**Change default from 8K → 6K:**

```python
# koderz/models/local.py
def __init__(
    self,
    num_ctx: int = 6144  # Reduced from 8192
):
```

**Reasoning:**
- ✅ Handles checkpoint iterations (5.8K max)
- ✅ Comfortable headroom for error iterations (4K typical)
- ✅ Saves memory vs 8K
- ✅ Still configurable via CLI if needed

Would you like me to update the code to use 6K instead of 8K?
