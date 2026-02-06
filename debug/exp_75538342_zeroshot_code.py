def right_angle_triangle(a, b, c):
    '''
    Given the lengths of the three sides of a triangle. Return True if the three
    sides form a right-angled triangle, False otherwise.
    '''
    import math
    try:
        sides = [float(a), float(b), float(c)]
    except (TypeError, ValueError):
        return False
    sides.sort()
    x, y, z = sides
    # Must be positive lengths and satisfy triangle inequality
    if x <= 0 or x + y <= z:
        return False
    return math.isclose(x * x + y * y, z * z, rel_tol=1e-9, abs_tol=1e-9)