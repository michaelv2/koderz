def prod_signs(arr):
    if not arr:
        return None
    total_mag = 0
    prod = 1
    for x in arr:
        total_mag += abs(x)
        if x == 0:
            return 0
        prod *= 1 if x > 0 else -1
    return total_mag * prod