def is_simple_power(x, n):
    """Return True if there exists an integer k >= 0 such that n**k == x."""
    # Handle special bases to avoid infinite loops or ambiguous cases.
    if n == 1:
        return x == 1
    if n == -1:
        return x == 1 or x == -1
    # Check k = 0 case
    if x == 1:
        return True
    # Handle zero cases
    if x == 0:
        # 0**k == 0 for k >= 1, so true iff base is 0 (there exists k>=1)
        return n == 0
    power = 1
    # Iterate multiplying by n until we either hit x or exceed its magnitude
    while True:
        power *= n
        if power == x:
            return True
        if power == 0:
            return False
        if abs(power) > abs(x):
            return False