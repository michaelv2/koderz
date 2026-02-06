def sorted_list_sum(lst):
    # Filter out the strings with odd lengths
    lst = [s for s in lst if len(s) % 2 == 0]
    
    # Sort by length and then alphabetically
    lst.sort()
    lst.sort(key=len)
    
    return lst