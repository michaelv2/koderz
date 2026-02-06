def special_factorial(n):
    """
    Brazilian factorial: product of all factorials from 1! up to n!
    i.e., n! * (n-1)! * ... * 1!
    """
    res = 1
    fact = 1
    for k in range(1, n + 1):
        fact *= k
        res *= fact
    return res