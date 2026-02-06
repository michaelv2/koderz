def fib4(n: int) -> int:
    if n <= 1:
        return 0
    elif n == 2:
        return 2

    fib = [0] * (n + 1)
    fib[2] = 2

    for i in range(4, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2] + fib[i - 3] + fib[i - 4]

    return fib[n]