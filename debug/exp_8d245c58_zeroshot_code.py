def iscube(a):
    if a == 0:
        return True
    
    # Handle negative numbers
    if a < 0:
        # For negative numbers, check if the absolute value is a perfect cube
        # and return True since negative numbers can be cubes of negative integers
        abs_a = -a
        cube_root = round(abs_a ** (1/3))
        return cube_root ** 3 == abs_a
    
    # Handle positive numbers
    cube_root = round(a ** (1/3))
    return cube_root ** 3 == a