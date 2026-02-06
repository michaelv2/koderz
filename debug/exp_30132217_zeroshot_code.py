def triangle_area(a, b, c):
    a, b, c = float(a), float(b), float(c)
    if a <= 0 or b <= 0 or c <= 0:
        return -1
    if a + b <= c or a + c <= b or b + c <= a:
        return -1
    s = (a + b + c) / 2.0
    from math import sqrt
    area = sqrt(s * (s - a) * (s - b) * (s - c))
    return round(area, 2)