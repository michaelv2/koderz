def prod_signs(arr):
    if arr is None or len(arr) == 0:
        return None
    total = 0
    prod = 1
    for x in arr:
        total += abs(x)
        if x == 0:
            prod = 0
        elif x > 0:
            prod *= 1
        else:
            prod *= -1
    return total * prod