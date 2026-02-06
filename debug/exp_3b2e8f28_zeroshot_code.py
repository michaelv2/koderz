def prod_signs(arr):
    """
    Given an array of integers, return the sum of magnitudes multiplied by
    the product of the signs of all elements. Signs are represented as:
    1 for positive, -1 for negative, and 0 for zero. If the array is empty,
    return None.
    """
    if not arr:
        return None

    total = 0
    prod = 1
    for x in arr:
        total += abs(x)
        if x > 0:
            prod *= 1
        elif x < 0:
            prod *= -1
        else:
            prod *= 0

    return total * prod