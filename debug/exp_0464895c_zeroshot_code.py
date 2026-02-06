def solution(lst):
    """Return the sum of odd elements located at even indices (0-based)."""
    return sum(x for i, x in enumerate(lst) if i % 2 == 0 and x % 2 != 0)