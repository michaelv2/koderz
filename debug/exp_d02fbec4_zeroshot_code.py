def x_or_y(n, x, y):
    """Return x if n is prime, otherwise return y."""
    # Only integers greater than 1 can be prime
    if not isinstance(n, int):
        return y
    if n <= 1:
        return y
    if n <= 3:
        return x
    if n % 2 == 0:
        return y
    i = 3
    while i * i <= n:
        if n % i == 0:
            return y
        i += 2
    return x