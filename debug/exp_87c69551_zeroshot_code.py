def pluck(arr):
    """
    Returns [value, index] of the smallest even value in arr.
    If multiple occurrences of the same smallest even value exist,
    the one with the smallest index is chosen. If there are no
    even values or the array is empty, returns [].
    """
    best_val = None
    best_index = -1
    for i, v in enumerate(arr):
        if v % 2 == 0:
            if best_val is None or v < best_val:
                best_val = v
                best_index = i
    if best_val is None:
        return []
    return [best_val, best_index]