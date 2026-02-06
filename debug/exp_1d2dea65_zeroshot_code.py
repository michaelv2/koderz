def fib4(n):
    if n < 0:
        return "Input should be non-negative"
    elif n == 0 or n == 1:
        return 0
    elif n == 2:
        return 2
    else:
        a, b, c, d = 0, 0, 2, 0
        for _ in range(n - 3):
            a, b, c, d = b, c, d, a + b + c + d
        return d