def f(n):
    """Return a list of length n where the i-th element (1-based) is:
       - factorial(i) if i is even
       - sum(1..i) if i is odd
    """
    res = []
    fact = 1
    for i in range(1, n + 1):
        fact *= i
        if i % 2 == 0:
            res.append(fact)
        else:
            res.append(i * (i + 1) // 2)
    return res