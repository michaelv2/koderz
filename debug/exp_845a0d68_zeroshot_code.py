def fib(n: int):
    """Return the n-th Fibonacci number (F(0)=0, F(1)=1)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a