def intersection(interval1, interval2):
    a, b = interval1
    c, d = interval2
    start = max(a, c)
    end = min(b, d)
    if start > end:
        return "NO"
    length = end - start
    if length <= 1:
        return "NO"
    if length == 2:
        return "YES"
    if length % 2 == 0:
        return "NO"
    r = int(length**0.5)
    i = 3
    while i <= r:
        if length % i == 0:
            return "NO"
        i += 2
    return "YES"