def fib4(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")

    # Base cases
    if n == 0 or n == 1 or n == 3:
        return 0
    if n == 2:
        return 2

    # Initialize for i = 4 with last = [f(i-1), f(i-2), f(i-3), f(i-4)]
    last = [0, 2, 0, 0]  # corresponds to [f(3), f(2), f(1), f(0)]
    for _ in range(4, n + 1):
        val = last[0] + last[1] + last[2] + last[3]
        last = [val, last[0], last[1], last[2]]
    return last[0]