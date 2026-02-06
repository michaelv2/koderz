def fib(n: int):
    """Return n-th Fibonacci number."""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    a, b = 0, 1
    for _ in range(1, n):
        a, b = b, a + b
    return b