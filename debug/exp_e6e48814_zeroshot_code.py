def cycpattern_check(a, b):
    """Return True if the second word or any of its rotations is a substring of the first word."""
    la, lb = len(a), len(b)
    if lb == 0:
        return True
    if lb > la:
        return False
    bb = b + b
    for i in range(lb):
        if a.find(bb[i:i+lb]) != -1:
            return True
    return False