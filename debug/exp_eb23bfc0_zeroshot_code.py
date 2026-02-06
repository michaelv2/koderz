def right_angle_triangle(a, b, c):
    # Sort the sides so that 'c' is always the longest side
    a, b, c = sorted([a, b, c])
    
    # A triangle is right-angled if and only if the square of the longest side (hypotenuse) 
    # equals to the sum of squares of the other two sides.
    return c**2 == a**2 + b**2