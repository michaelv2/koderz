def maximum(arr, k):
    # Step 1: Sort the array in descending order
    arr.sort(reverse=True)
    
    # Step 2: Select the top k elements
    top_k_elements = arr[:k]
    
    # Step 3: Sort the selected elements in ascending order
    top_k_elements.sort()
    
    return top_k_elements