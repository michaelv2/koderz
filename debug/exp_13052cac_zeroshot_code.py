def strange_sort_list(lst):
    sorted_list = []
    lst.sort()  # Sort the list to easily access min and max
    
    while lst:
        if sorted_list:  # If there's already an element in the result, take the maximum
            sorted_list.append(lst.pop())
        else:  # Otherwise, take the minimum
            sorted_list.append(lst.pop(0))
    
    return sorted_list