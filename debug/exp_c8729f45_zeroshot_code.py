def right_angle_triangle(a, b, c):
    # Sort the sides to identify the hypotenuse
    sides = sorted([a, b, c])
    # Check if the square of the largest side is equal to the sum of the squares of the other two sides
    return sides[2]**2 == sides[0]**2 + sides[1]**2