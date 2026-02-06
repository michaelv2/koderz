def cycpattern_check(a, b):
    if not b:
        return True
    
    # Generate all rotations of b
    for i in range(len(b)):
        rotation = b[i:] + b[:i]
        if rotation in a:
            return True
    
    return False