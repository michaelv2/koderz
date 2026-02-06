def smallest_change(arr):
    n = len(arr)
    i, j = 0, n - 1
    changes = 0
    while i < j:
        if arr[i] != arr[j]:
            changes += 1
        i += 1
        j -= 1
    return changes