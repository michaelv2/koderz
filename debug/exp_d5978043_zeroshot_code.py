def sorted_list_sum(lst):
    # Filter strings with even lengths only
    even_length_strings = [s for s in lst if len(s) % 2 == 0]
    
    # Sort by length first, then alphabetically
    sorted_result = sorted(even_length_strings, key=lambda x: (len(x), x))
    
    return sorted_result