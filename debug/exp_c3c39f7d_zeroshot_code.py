def digits(n):
    """Given a positive integer n, return the product of the odd digits.
    Return 0 if all digits are even."""
    prod = 1
    found = False
    if n == 0:
        return 0
    while n:
        d = n % 10
        if d % 2 == 1:
            prod *= d
            found = True
        n //= 10
    return prod if found else 0