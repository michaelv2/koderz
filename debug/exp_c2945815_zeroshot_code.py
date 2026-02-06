def is_simple_power(x, n):
    # Handle edge case where n is 1
    if n == 1:
        return x == 1
    
    # Handle edge case where n is 0
    if n == 0:
        return x == 0
    
    # Handle negative n - we need to be careful
    if n < 0:
        n = -n
        # For negative base, only odd powers give negative results
        if x < 0:
            x = -x
        else:
            return False
    
    # Handle x = 1 (which is n^0 for any n)
    if x == 1:
        return True
    
    # If x is negative and n is positive, x cannot be a power of n
    if x < 0:
        return False
    
    # Repeatedly divide x by n
    while x > 1:
        if x % n == 0:
            x //= n
        else:
            return False
    
    return x == 1