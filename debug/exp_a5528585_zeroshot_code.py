def maximum(arr, k):
    arr.sort()
    return sorted(arr[-k:], reverse=True)