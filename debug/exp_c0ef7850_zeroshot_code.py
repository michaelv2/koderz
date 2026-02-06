def is_simple_power(x, n):
    """
    Return True if x is a simple power of n, i.e., there exists a non-negative integer k
    such that n**k == x.
    """
    try:
        x = int(x)
        n = int(n)
    except Exception:
        return False

    if n == 1:
        return x == 1
    if x == 1:
        return True
    if n <= 0:
        if n == 0:
            # 0**k is 0 for k>0; 0**0 is treated as 1 in this context
            return x in (0, 1)
        return False

    while x > 1 and x % n == 0:
        x //= n
    return x == 1