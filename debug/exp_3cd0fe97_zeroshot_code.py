def maximum(arr, k):
    """
    Return a sorted list of length k containing the largest k numbers from arr.
    The result is sorted in non-decreasing order.
    """
    if k <= 0:
        return []
    top = sorted(arr, reverse=True)[:k]
    return sorted(top)