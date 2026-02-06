def add_elements(arr, k):
    total = 0
    for i in range(k):
        if arr[i] <= 99:
            total += arr[i]
    return total