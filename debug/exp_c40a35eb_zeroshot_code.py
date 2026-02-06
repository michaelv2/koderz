def add_elements(arr, k):
    # Extract the first k elements
    first_k_elements = arr[:k]
    
    # Filter out elements with more than two digits
    filtered_elements = [x for x in first_k_elements if -99 <= x <= 99]
    
    # Sum the remaining elements
    return sum(filtered_elements)