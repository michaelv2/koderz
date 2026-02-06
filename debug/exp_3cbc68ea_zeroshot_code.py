def fib4(n: int):
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 2
    if n == 3:
        return 0
    prev4, prev3, prev2, prev1 = 0, 0, 2, 0
    for _ in range(4, n + 1):
        curr = prev1 + prev2 + prev3 + prev4
        prev4, prev3, prev2, prev1 = prev3, prev2, prev1, curr
    return prev1