def median(l: list):
    l_sorted = sorted(l)
    n = len(l_sorted)
    mid = n // 2
    if n % 2 == 1:
        return l_sorted[mid]
    else:
        return (l_sorted[mid - 1] + l_sorted[mid]) / 2.0