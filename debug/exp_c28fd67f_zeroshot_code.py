def iscube(a):
    if a == 0:
        return True
    
    # Find the cube root of the absolute value
    cube_root = round(abs(a) ** (1/3))
    
    # Check if cube_root cubed equals a
    if cube_root ** 3 == a:
        return True
    
    # Due to floating point precision, also check nearby integers
    for offset in [-1, 1]:
        if (cube_root + offset) ** 3 == a:
            return True
    
    return False