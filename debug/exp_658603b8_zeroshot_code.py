def pluck(arr):
    """
    Returns the smallest even value and its index, or empty list if no even values.
    """
    if not arr:
        return []
    
    smallest_even = None
    smallest_index = None
    
    for i, num in enumerate(arr):
        # Check if the number is even
        if num % 2 == 0:
            # If this is the first even number or smaller than the current smallest even
            if smallest_even is None or num < smallest_even:
                smallest_even = num
                smallest_index = i
    
    # Return the result or empty list
    if smallest_even is not None:
        return [smallest_even, smallest_index]
    else:
        return []