def change_base(x: int, base: int):
    if x == 0:
        return '0'
    sign = '-' if x < 0 else ''
    n = abs(x)
    digits = []
    while n:
        digits.append(str(n % base))
        n //= base
    return sign + ''.join(reversed(digits))