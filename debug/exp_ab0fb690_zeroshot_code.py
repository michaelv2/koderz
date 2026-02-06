def sort_array(array):
    # Handle edge cases
    if len(array) <= 1:
        return array.copy()
    
    # Calculate sum of first and last elements
    sum_first_last = array[0] + array[-1]
    
    # Create a copy of the array to avoid modifying the original
    result = array.copy()
    
    # Sort based on whether the sum is odd or even
    if sum_first_last % 2 == 1:  # odd
        result.sort()  # ascending order
    else:  # even
        result.sort(reverse=True)  # descending order
    
    return result