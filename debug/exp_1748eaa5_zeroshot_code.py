def pluck(arr):
    if not arr:
        return []
    
    smallest_even = None
    smallest_index = -1
    
    for i, node in enumerate(arr):
        if node % 2 == 0:  # Check if node is even
            if smallest_even is None or node < smallest_even:
                smallest_even = node
                smallest_index = i
    
    if smallest_even is None:
        return []
    
    return [smallest_even, smallest_index]