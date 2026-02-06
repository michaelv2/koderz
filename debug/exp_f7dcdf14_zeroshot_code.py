def maximum(arr, k):
    # Sort in descending order to get largest elements, take first k, then sort ascending
    return sorted(sorted(arr, reverse=True)[:k])