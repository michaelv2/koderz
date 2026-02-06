def right_angle_triangle(a, b, c):
    # Sort the side lengths in ascending order
    sides = sorted([a, b, c])

    # Check if it forms a right-angled triangle using Pythagorean theorem
    return sides[2]**2 == sides[0]**2 + sides[1]**2