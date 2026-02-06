def next_smallest(lst):
    # Remove duplicates by converting the list to a set and back to a list
    unique_lst = list(set(lst))
    
    # Sort the list
    unique_lst.sort()
    
    # Check if there are at least two elements
    if len(unique_lst) < 2:
        return None
    
    # Return the second smallest element
    return unique_lst[1]