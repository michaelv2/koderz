def smallest_change(arr):
    """
    Given an array arr of integers, return the minimum number of elements that
    need to be changed to make the array palindromic.
    """
    return sum(1 for i in range(len(arr) // 2) if arr[i] != arr[-1 - i])