def sort_even(l: list):
    # Extract elements at even indices
    even_index_elements = [l[i] for i in range(0, len(l), 2)]
    
    # Sort the extracted elements
    even_index_elements.sort()
    
    # Create a new list to store the result
    result = l[:]
    
    # Place sorted even-indexed elements back into their positions
    even_index = 0
    for i in range(0, len(l), 2):
        result[i] = even_index_elements[even_index]
        even_index += 1
    
    return result