def median(l: list):
    """Return the median of the numbers in l.
    Raises ValueError if l is empty.
    """
    if not l:
        raise ValueError("median() arg is an empty sequence")
    s = sorted(l)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    else:
        return (s[mid - 1] + s[mid]) / 2