def is_simple_power(x, n):
    """Return True if x is a simple power of n (x == n**k for some integer k >= 0)."""
    try:
        x = int(x)
        n = int(n)
    except (ValueError, TypeError):
        return False

    if n == 0:
        # 0**0 is treated as 1 in Python; valid powers for n=0 are 1 (k=0) and 0 (k>=1)
        return x == 0 or x == 1
    if n == 1:
        return x == 1
    if x == 1:
        return True  # n**0 = 1 for any n != 0
    if x == 0:
        return False
    if n == -1:
        return x == 1 or x == -1

    cur = 1
    while True:
        cur *= n
        if cur == x:
            return True
        if abs(cur) > abs(x):
            return False
        if cur == 0:
            return False