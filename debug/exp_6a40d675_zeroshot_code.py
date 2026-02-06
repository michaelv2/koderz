def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    """
    s = str(x)
    sign = ''
    if s.startswith('-'):
        sign = '-'
        s = s[1:]
    n = len(s)
    if shift > n:
        return sign + s[::-1]
    # handle shift possibly larger than n via modulo, but preserve behavior when shift == n
    if n == 0:
        return sign + s
    shift = shift % n
    if shift == 0:
        return sign + s
    return sign + (s[-shift:] + s[:-shift])