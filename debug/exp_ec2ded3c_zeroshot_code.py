def sort_array(array):
    # Check if the array is empty or has only one element
    if len(array) < 2:
        return array[:]
    
    # Calculate the sum of first and last elements
    total = array[0] + array[-1]
    
    # Sort in ascending order if the sum is odd, otherwise sort in descending order
    sorted_array = sorted(array) if total % 2 != 0 else sorted(array, reverse=True)
    
    return sorted_array