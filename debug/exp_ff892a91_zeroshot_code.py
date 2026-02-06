def right_angle_triangle(a, b, c):
    '''
    Given the lengths of the three sides of a triangle. Return True if the three
    sides form a right-angled triangle, False otherwise.
    '''
    try:
        sides = [float(a), float(b), float(c)]
    except (TypeError, ValueError):
        return False
    # All sides must be positive
    if any(s <= 0 for s in sides):
        return False
    sides.sort()
    # Triangle inequality: sum of smaller two must be greater than the largest
    if sides[0] + sides[1] <= sides[2]:
        return False
    # Check Pythagorean theorem with a tolerance for floating point inputs
    tol = 1e-9
    return abs(sides[0]**2 + sides[1]**2 - sides[2]**2) <= tol