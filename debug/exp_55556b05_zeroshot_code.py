def smallest_change(arr):
    """
    Return the minimum number of elements to change to make arr palindromic.
    Each change can set one element to any value.
    """
    i, j = 0, len(arr) - 1
    changes = 0
    while i < j:
        if arr[i] != arr[j]:
            changes += 1
        i += 1
        j -= 1
    return changes