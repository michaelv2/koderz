def fibfib(n: int) -> int:
    if n < 3:
        return [0, 0, 1][n]

    fib = [0, 0, 1] + [0] * (n - 2)
    for i in range(3, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2] + fib[i - 3]

    return fib[n]