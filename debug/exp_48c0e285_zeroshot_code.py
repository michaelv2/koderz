def change_base(x: int, base: int):
    """Change numerical base of input number x to base.
    return string representation after the conversion.
    base numbers are less than 10.
    >>> change_base(8, 3)
    '22'
    >>> change_base(8, 2)
    '1000'
    >>> change_base(7, 2)
    '111'
    """
    if not (2 <= base < 10):
        raise ValueError("base must be between 2 and 9 inclusive")
    if x == 0:
        return "0"
    neg = x < 0
    n = -x if neg else x
    digits = []
    while n:
        digits.append(str(n % base))
        n //= base
    result = "".join(reversed(digits))
    return "-" + result if neg else result