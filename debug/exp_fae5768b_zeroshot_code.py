def maximum(arr, k):
    """
    Return a sorted list of length k containing the largest k numbers from arr.
    The result is sorted in ascending order.
    """
    if k == 0:
        return []
    largest_k = sorted(arr, reverse=True)[:k]
    return sorted(largest_k)