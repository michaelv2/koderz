def maximum(arr, k):
    """
    Given an array arr of integers and a positive integer k, return a sorted list 
    of length k with the maximum k numbers in arr.
    """
    if k == 0:
        return []
    # Sort ascending and take the last k elements (they will be in ascending order)
    return sorted(arr)[-k:]