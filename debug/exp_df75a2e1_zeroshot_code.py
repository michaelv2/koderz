def intersection(interval1, interval2):
    a1, b1 = interval1
    a2, b2 = interval2
    left = max(a1, a2)
    right = min(b1, b2)
    if left > right:
        return "NO"
    length = right - left
    if length <= 1:
        return "NO"
    if length == 2:
        return "YES"
    if length % 2 == 0:
        return "NO"
    i = 3
    import math
    limit = int(math.isqrt(length))
    while i <= limit:
        if length % i == 0:
            return "NO"
        i += 2
    return "YES"