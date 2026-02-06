import math

def triangle_area(a, b, c):
    '''
    Given the lengths of the three sides of a triangle. Return the area of
    the triangle rounded to 2 decimal points if the three sides form a valid triangle. 
    Otherwise return -1
    '''
    # Check triangle inequality
    if not (a + b > c and a + c > b and b + c > a):
        return -1
    s = (a + b + c) / 2.0
    area_sq = s * (s - a) * (s - b) * (s - c)
    # Protect against tiny negative due to floating point
    if area_sq < 0:
        if area_sq > -1e-12:
            area_sq = 0.0
        else:
            return -1
    area = math.sqrt(area_sq)
    return round(area, 2)