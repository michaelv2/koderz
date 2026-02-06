def strange_sort_list(lst):
    result = []
    while lst:
        # Get and remove the minimum value from list
        min_val = min(lst)
        lst.remove(min_val)
        result.append(min_val)
        
        if lst:  # If there are still elements in the list
            # Get and remove the maximum value from list
            max_val = max(lst)
            lst.remove(max_val)
            result.append(max_val)
            
    return result