def sort_array(array):
    if not array:
        return []
    
    # Determine the sorting order based on the sum of the first and last elements
    if (array[0] + array[-1]) % 2 == 0:
        sorted_array = sorted(array, reverse=True)
    else:
        sorted_array = sorted(array)
    
    return sorted_array