def fib4(n: int) -> int:
    """Compute the n-th term of the Fib4 sequence without recursion.

    Base cases:
      fib4(0) = 0
      fib4(1) = 0
      fib4(2) = 2
      fib4(3) = 0

    For n >= 4:
      fib4(n) = fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)
    """
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

    a0, a1, a2, a3 = 0, 0, 2, 0  # fib4(0), fib4(1), fib4(2), fib4(3)
    for i in range(4, n + 1):
        val = a3 + a2 + a1 + a0  # fib4(i) = fib4(i-1) + fib4(i-2) + fib4(i-3) + fib4(i-4)
        a0, a1, a2, a3 = a1, a2, a3, val
    return a3