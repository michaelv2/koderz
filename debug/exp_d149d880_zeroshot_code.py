import math

def triangle_area(a, b, c):
    # Check for a valid triangle
    if a + b <= c or a + c <= b or b + c <= a:
        return -1
    
    # Calculate the semi-perimeter
    s = (a + b + c) / 2
    
    # Calculate the area using Heron's formula
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    
    # Return the area rounded to 2 decimal places
    return round(area, 2)