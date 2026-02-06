def change_base(x: int, base: int):
    """Return string representation of integer x in the given base (2 <= base <= 9).
    If x is 0, return '0'. Supports negative integers by prefixing with '-'.
    """
    if base < 2 or base > 9:
        raise ValueError("base must be between 2 and 9 inclusive")
    if x == 0:
        return '0'
    sign = '-' if x < 0 else ''
    n = abs(x)
    digits = []
    while n:
        digits.append(str(n % base))
        n //= base
    return sign + ''.join(reversed(digits))