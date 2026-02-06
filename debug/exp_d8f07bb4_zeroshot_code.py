def fib4(n: int):
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 2
    if n == 3:
        return 0
    a, b, c, d = 0, 0, 2, 0  # fib4(0), fib4(1), fib4(2), fib4(3)
    for _ in range(4, n + 1):
        a, b, c, d = b, c, d, a + b + c + d
    return d