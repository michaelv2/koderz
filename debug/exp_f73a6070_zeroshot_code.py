def f(n):
    """Return a list of size n where element at index i-1 is:
    - factorial(i) if i is even
    - sum 1..i if i is odd
    """
    res = []
    fact = 1
    s = 0
    for i in range(1, n + 1):
        fact *= i
        s += i
        if i % 2 == 0:
            res.append(fact)
        else:
            res.append(s)
    return res