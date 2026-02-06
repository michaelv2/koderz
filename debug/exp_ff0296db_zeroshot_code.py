def any_int(x, y, z):
    """
    Return True if all inputs are integers and one value equals
    the sum of the other two; otherwise return False.
    """
    if not (isinstance(x, int) and isinstance(y, int) and isinstance(z, int)):
        return False
    return x == y + z or y == x + z or z == x + y