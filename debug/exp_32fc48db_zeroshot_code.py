def sum_to_n(n: int):
    """Sum of integers from 1 to n inclusive. Returns 0 for non-positive n."""
    if n <= 0:
        return 0
    return n * (n + 1) // 2