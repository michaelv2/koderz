def monotonic(l: list):
    """Return True if the list elements are monotonically increasing or decreasing."""
    if len(l) <= 1:
        return True
    inc = all(l[i] <= l[i + 1] for i in range(len(l) - 1))
    dec = all(l[i] >= l[i + 1] for i in range(len(l) - 1))
    return inc or dec