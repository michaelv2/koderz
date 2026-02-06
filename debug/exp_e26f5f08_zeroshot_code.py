def make_a_pile(n):
    """
    Given a positive integer n, return a list of length n where the first element
    is n and each subsequent element is the next odd (if starting odd) or next
    even (if starting even) number. This is equivalent to n, n+2, n+4, ...
    """
    return [n + 2 * i for i in range(n)]