def is_simple_power(x, n):
    # Handle special bases first
    if n == 0:
        # 0**k == 0 for k >= 1, 0**0 is undefined; treat only x==0 as a valid positive exponent power
        return x == 0
    if n == 1:
        return x == 1
    if n == -1:
        return x == 1 or x == -1

    # For other n, handle x == 1 (n**0 == 1 for any nonzero n)
    if x == 1:
        return True

    # Nonzero base other than ±1 and 0:
    # If base > 1, powers are >= 1 and positive
    if n > 1:
        if x < 1:
            return False
        # Repeatedly divide out factors of n
        while x % n == 0:
            x //= n
        return x == 1

    # If base < -1, powers alternate sign depending on exponent parity
    if n < -1:
        if x == 0:
            return False
        base = abs(n)
        sign_negative = x < 0
        x_abs = abs(x)
        exp = 0
        while x_abs % base == 0:
            x_abs //= base
            exp += 1
        if x_abs != 1:
            return False
        # If x was negative, exponent must be odd; if positive, exponent must be even
        return (exp % 2 == 1) if sign_negative else (exp % 2 == 0)