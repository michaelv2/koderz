def fib4(n: int):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1 or n == 3:
        return 0
    if n == 2:
        return 2
    a, b, c, d = 0, 0, 2, 0  # f(n-4), f(n-3), f(n-2), f(n-1) for current n=4
    for _ in range(4, n + 1):
        nxt = a + b + c + d
        a, b, c, d = b, c, d, nxt
    return d