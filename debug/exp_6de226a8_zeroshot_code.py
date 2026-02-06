def right_angle_triangle(a, b, c):
    # Check if all sides are positive
    if a <= 0 or b <= 0 or c <= 0:
        return False
    
    # Sort the sides to identify the longest side
    sides = sorted([a, b, c])
    
    # Check if Pythagorean theorem holds: a² + b² = c²
    # where c is the longest side
    return abs(sides[0]**2 + sides[1]**2 - sides[2]**2) < 1e-10