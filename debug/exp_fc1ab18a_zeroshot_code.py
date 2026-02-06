def tri(n):
    """Return a list of the first n+1 Tribonacci numbers as defined."""
    if n < 0:
        raise ValueError("n must be non-negative")
    res = [0] * (n + 1)
    # given values
    if n >= 0:
        res[0] = 1
    if n >= 1:
        res[1] = 3
    for k in range(2, n + 1):
        if k % 2 == 0:  # even
            res[k] = 1 + k // 2
        else:  # odd
            # tri(k) = tri(k-1) + tri(k-2) + tri(k+1)
            # but k+1 is even so tri(k+1) = 1 + (k+1)/2
            res[k] = res[k - 1] + res[k - 2] + (1 + (k + 1) // 2)
    return res