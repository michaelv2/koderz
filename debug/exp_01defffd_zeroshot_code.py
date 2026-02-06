def pluck(arr):
    min_even = float('inf')
    min_index = -1

    for i in range(len(arr)):
        if arr[i] % 2 == 0 and arr[i] < min_even:
            min_even = arr[i]
            min_index = i

    return [min_even, min_index] if min_index != -1 else []