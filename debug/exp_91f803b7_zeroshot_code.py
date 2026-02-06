def prod_signs(arr):
    if arr is None or len(arr) == 0:
        return None
    sum_mag = 0
    prod = 1
    for x in arr:
        if x == 0:
            return 0
        sum_mag += abs(x)
        if x < 0:
            prod = -prod
    return sum_mag * prod