def make_a_pile(n):
    """
    Given a positive integer n, return a list of length n where the first element
    is n and each subsequent element is the next odd number if n is odd or the
    next even number if n is even.
    """
    return [n + 2 * i for i in range(n)]