def cycpattern_check(a, b):
    """Check if b or any rotation of b is a substring of a"""
    if len(b) > len(a):
        return False
    
    # Check all rotations of b
    for i in range(len(b)):
        rotation = b[i:] + b[:i]
        if rotation in a:
            return True
    
    return False