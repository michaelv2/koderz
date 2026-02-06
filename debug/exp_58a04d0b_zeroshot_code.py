def right_angle_triangle(a, b, c):
    sides = sorted([a, b, c])
    x, y, z = sides
    if x <= 0:
        return False
    return abs(x * x + y * y - z * z) <= 1e-9