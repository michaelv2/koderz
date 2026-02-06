def sort_even(l: list):
    # Extract elements at even indices
    even_elements = [l[i] for i in range(0, len(l), 2)]
    
    # Sort the extracted even elements
    even_elements.sort()
    
    # Reconstruct the new list with sorted even elements and unchanged odd elements
    result = []
    even_index = 0
    for i in range(len(l)):
        if i % 2 == 0:
            result.append(even_elements[even_index])
            even_index += 1
        else:
            result.append(l[i])
    
    return result