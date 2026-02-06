import math

def triangle_area(a, b, c):
    # Check if the three sides can form a valid triangle
    if (a + b > c) and (b + c > a) and (c + a > b):
        # Calculate semi-perimeter
        s = (a + b + c) / 2.0
        # Use Heron's formula to calculate the area
        return round(math.sqrt(s * (s - a) * (s - b) * (s - c)), 2)
    else:
        return -1