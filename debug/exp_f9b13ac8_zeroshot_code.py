def is_simple_power(x, n):
    """Return True if x is a power of n with a non-negative integer exponent."""
    try:
        x = int(x)
        n = int(n)
    except Exception:
        return False

    # Handle some edge cases
    if x == 0:
        return n == 0  # 0 can be obtained as 0**k for k>=1; here we consider 0**1
                       # as a valid case only when n == 0
    if x == 1:
        return n != 0  # n**0 == 1 for any n != 0
    if n == 0:
        return False
    if n == 1:
        return x == 1
    if n == -1:
        return x in (1, -1)

    value = 1
    seen = set()
    while True:
        if value == x:
            return True
        if abs(value) > abs(x):
            return False
        if value in seen:
            return False
        seen.add(value)
        value *= n
        if len(seen) > 1000:
            return False