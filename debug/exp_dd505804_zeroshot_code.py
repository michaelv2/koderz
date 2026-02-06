def smallest_change(arr):
    n = len(arr)
    changes = 0
    
    # Compare elements from both ends moving towards center
    for i in range(n // 2):
        if arr[i] != arr[n - 1 - i]:
            changes += 1
    
    return changes