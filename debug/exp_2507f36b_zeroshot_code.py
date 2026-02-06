def pluck(arr):
    smallest_even = None
    smallest_index = -1
    
    for i, value in enumerate(arr):
        if value % 2 == 0:  # Check if the number is even
            if smallest_even is None or value < smallest_even:
                smallest_even = value
                smallest_index = i
    
    if smallest_even is not None:
        return [smallest_even, smallest_index]
    else:
        return []