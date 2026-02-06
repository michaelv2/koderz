def next_smallest(lst):
    if not lst:
        return None
    
    # Get unique elements and sort them
    unique_sorted = sorted(set(lst))
    
    # Check if we have at least 2 unique elements
    if len(unique_sorted) < 2:
        return None
    
    # Return the second smallest unique element
    return unique_sorted[1]