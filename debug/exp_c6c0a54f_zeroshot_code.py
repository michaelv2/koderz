def maximum(arr, k):
    """
    Given an array arr of integers and a positive integer k, return a sorted list
    of length k with the maximum k numbers in arr.
    """
    if k <= 0:
        return []
    arr_sorted = sorted(arr)
    return arr_sorted[-k:]