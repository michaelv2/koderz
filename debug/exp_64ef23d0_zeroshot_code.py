def monotonic(l: list):
    """Return True if list elements are monotonically increasing or decreasing.
    A sequence is monotonic if it is either non-decreasing or non-increasing.
    """
    if len(l) < 2:
        return True
    inc = all(l[i] <= l[i + 1] for i in range(len(l) - 1))
    dec = all(l[i] >= l[i + 1] for i in range(len(l) - 1))
    return inc or dec