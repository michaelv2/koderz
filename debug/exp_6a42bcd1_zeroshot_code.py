def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    >>> circular_shift(12, 1)
    "21"
    >>> circular_shift(12, 2)
    "12"
    """
    s = str(x)
    sign = ''
    if s.startswith('-'):
        sign = '-'
        s = s[1:]
    n = len(s)
    if n == 0:
        return sign
    if shift > n:
        rotated = s[::-1]
    else:
        k = shift % n
        if k == 0:
            rotated = s
        else:
            rotated = s[-k:] + s[:-k]
    return sign + rotated