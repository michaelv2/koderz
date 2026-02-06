def f(n):
    """Return a list of length n where the value at position i-1 is:
    - the factorial of i if i is even
    - the sum 1 + 2 + ... + i if i is odd
    with i starting from 1.
    """
    if n <= 0:
        return []
    res = []
    fact = 1
    s = 0
    for i in range(1, n + 1):
        s += i
        fact *= i
        if i % 2 == 0:
            res.append(fact)
        else:
            res.append(s)
    return res