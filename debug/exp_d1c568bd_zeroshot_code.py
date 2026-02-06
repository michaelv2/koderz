def prod_signs(arr):
    if not arr:
        return None
    sign = 1
    for x in arr:
        if x == 0:
            return 0
        if x < 0:
            sign = -sign
    return sign * sum(abs(x) for x in arr)