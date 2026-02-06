def strange_sort_list(lst):
    sorted_lst = sorted(lst)
    result = []
    left = 0
    right = len(sorted_lst) - 1
    take_min = True
    
    while left <= right:
        if take_min:
            result.append(sorted_lst[left])
            left += 1
        else:
            result.append(sorted_lst[right])
            right -= 1
        take_min = not take_min
    
    return result