def maximum(arr, k):
    # Sort the array in descending order to get largest elements first
    sorted_arr = sorted(arr, reverse=True)
    
    # Take the first k elements (the k largest elements)
    k_largest = sorted_arr[:k]
    
    # Sort these k elements in ascending order for the final result
    return sorted(k_largest)