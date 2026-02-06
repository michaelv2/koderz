def largest_divisor(n: int) -> int:
    """Return the largest proper divisor of n (a divisor strictly smaller than n)."""
    if n <= 1:
        return 0
    limit = int(n ** 0.5)
    for d in range(2, limit + 1):
        if n % d == 0:
            return n // d
    return 1