def largest_divisor(n: int) -> int:
    """Return the largest divisor of n that is smaller than n.
    If n is prime (or n <= 1), returns 1.
    """
    if n <= 1:
        return 1
    limit = int(n ** 0.5)
    for i in range(2, limit + 1):
        if n % i == 0:
            return n // i
    return 1