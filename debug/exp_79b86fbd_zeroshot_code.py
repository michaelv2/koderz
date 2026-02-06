def digits(n):
    """Return the product of the odd digits of n; 0 if there are no odd digits."""
    product = 1
    found_odd = False
    while n > 0:
        d = n % 10
        if d % 2 == 1:
            product *= d
            found_odd = True
        n //= 10
    return product if found_odd else 0