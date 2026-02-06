def triangle_area(a, b, c):
    # Check if three sides form a valid triangle
    if a + b > c and a + c > b and b + c > a:
        # Calculate semi-perimeter
        s = (a + b + c) / 2
        # Use Heron's formula to calculate area
        area = (s * (s - a) * (s - b) * (s - c)) ** 0.5
        # Round to 2 decimal places
        return round(area, 2)
    else:
        return -1