def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    """
    s = str(x)
    if s.startswith('-'):
        sign = '-'
        digits = s[1:]
    else:
        sign = ''
        digits = s
    n = len(digits)
    if n == 0:
        return sign + digits
    if shift > n:
        result = digits[::-1]
    else:
        # Python handles shift==0 and shift==n correctly with slicing
        result = digits[-shift:] + digits[:-shift] if shift != 0 else digits
    return sign + result