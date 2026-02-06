def strange_sort_list(lst):
    if not lst:
        return []
    
    # Sort the list first
    sorted_lst = sorted(lst)
    result = []
    
    # Use two pointers
    left = 0
    right = len(sorted_lst) - 1
    pick_min = True  # Flag to alternate between min and max
    
    # Continue until all elements are picked
    while left <= right:
        if pick_min:
            result.append(sorted_lst[left])
            left += 1
        else:
            result.append(sorted_lst[right])
            right -= 1
        pick_min = not pick_min  # Alternate for next iteration
    
    return result