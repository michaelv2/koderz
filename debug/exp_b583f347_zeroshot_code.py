def monotonic(l: list):
    """Return True if the list elements are monotonically increasing or decreasing
    (non-strict, i.e., allows equal consecutive elements)."""
    if len(l) <= 1:
        return True
    increasing = all(l[i] <= l[i + 1] for i in range(len(l) - 1))
    decreasing = all(l[i] >= l[i + 1] for i in range(len(l) - 1))
    return increasing or decreasing