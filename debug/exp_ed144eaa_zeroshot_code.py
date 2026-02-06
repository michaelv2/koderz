def sort_even(l: list):
    # Extract elements at even indices
    even_index_elements = [l[i] for i in range(0, len(l), 2)]
    
    # Sort the extracted elements
    even_index_elements.sort()
    
    # Reconstruct the list with sorted even-indexed elements
    result = l[:]
    j = 0
    for i in range(0, len(l), 2):
        result[i] = even_index_elements[j]
        j += 1
    
    return result