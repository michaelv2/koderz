import math

def triangle_area(a, b, c):
    # Check if the given lengths can form a valid triangle
    if (a + b <= c) or (b + c <= a) or (c + a <= b):
        return -1

    # Calculate the semi-perimeter of the triangle
    s = (a + b + c) / 2

    # Use Heron's formula to calculate the area of the triangle
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))

    # Round the calculated area to 2 decimal points and return it
    return round(area, 2)