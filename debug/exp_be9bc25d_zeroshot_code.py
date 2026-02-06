def any_int(x, y, z):
    # Check if all three are integers (not bools, not floats)
    if not (isinstance(x, int) and isinstance(y, int) and isinstance(z, int)):
        return False
    if isinstance(x, bool) or isinstance(y, bool) or isinstance(z, bool):
        return False
    
    # Check if one of the numbers equals the sum of the other two
    if x == y + z or y == x + z or z == x + y:
        return True
    
    return False