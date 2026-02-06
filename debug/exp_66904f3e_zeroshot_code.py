def change_base(x: int, base: int):
    """Change numerical base of input number x to base.
    return string representation after the conversion.
    base numbers are less than 10.
    """
    if not isinstance(base, int) or base < 2 or base >= 10:
        raise ValueError("base must be an integer between 2 and 9 inclusive")
    if not isinstance(x, int):
        raise ValueError("x must be an integer")
    if x == 0:
        return "0"
    sign = ""
    if x < 0:
        sign = "-"
        x = -x
    digits = []
    while x > 0:
        digits.append(str(x % base))
        x //= base
    return sign + "".join(reversed(digits))