def iscube(a):
    # Calculate the cube root of a
    cube_root = round(a ** (1/3))
    # Check if cubing the rounded cube root gives back the original number
    return cube_root ** 3 == a