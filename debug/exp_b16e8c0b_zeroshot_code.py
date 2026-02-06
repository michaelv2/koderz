def fib(n: int):
    """Return the n-th Fibonacci number with F(1) = 1, F(2) = 1."""
    if n <= 0:
        return 0
    if n <= 2:
        return 1
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b