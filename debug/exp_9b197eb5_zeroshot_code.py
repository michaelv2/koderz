def strange_sort_list(lst):
    result = []
    while lst:
        # Append the minimum value
        min_val = min(lst)
        lst.remove(min_val)
        result.append(min_val)
        
        # Check if list is empty after removing min
        if not lst:
            break
        
        # Append the maximum value
        max_val = max(lst)
        lst.remove(max_val)
        result.append(max_val)
    
    return result