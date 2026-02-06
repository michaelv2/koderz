def iscube(a):
    # Calculate the cube root of 'a'
    cube_root = round(a ** (1/3))
    
    # Check if the cube of the rounded cube root equals 'a'
    return cube_root ** 3 == a