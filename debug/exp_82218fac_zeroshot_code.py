def sort_array(array):
    if not array:
        return []
    
    first_value = array[0]
    last_value = array[-1]
    
    if (first_value + last_value) % 2 == 0:
        return sorted(array, reverse=True)
    else:
        return sorted(array)