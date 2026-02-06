def any_int(x, y, z):
    # Check if all numbers are integers
    if not all(isinstance(num, int) for num in [x, y, z]):
        return False
    
    # Check if any number equals the sum of the other two
    return (x == y + z) or (y == x + z) or (z == x + y)