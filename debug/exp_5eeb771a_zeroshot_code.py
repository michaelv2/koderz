def prod_signs(arr):
    """
    You are given an array arr of integers and you need to return
    sum of magnitudes of integers multiplied by product of all signs
    of each number in the array, represented by 1, -1 or 0.
    Note: return None for empty arr.
    """
    if not arr:
        return None
    total = sum(abs(x) for x in arr)
    # If any zero present, product of signs is 0
    for x in arr:
        if x == 0:
            return 0
    # Determine overall sign by count of negative numbers
    neg_count = sum(1 for x in arr if x < 0)
    sign = -1 if (neg_count % 2 == 1) else 1
    return sign * total