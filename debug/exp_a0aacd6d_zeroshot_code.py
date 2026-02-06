def circular_shift(x, shift):
    s = str(x)
    if s.startswith('-'):
        sign = '-'
        digits = s[1:]
        n = len(digits)
        if n == 0:
            return sign
        if shift > n:
            return sign + digits[::-1]
        shift = shift % n
        if shift == 0:
            return sign + digits
        return sign + digits[-shift:] + digits[:-shift]
    else:
        n = len(s)
        if n == 0:
            return ""
        if shift > n:
            return s[::-1]
        shift = shift % n
        if shift == 0:
            return s
        return s[-shift:] + s[:-shift]