def sorted_list_sum(lst):
    # Filter out strings with odd lengths
    even_length_lst = [s for s in lst if len(s) % 2 == 0]
    
    # Sort the list by length of each word, and alphabetically for words of the same length
    sorted_lst = sorted(even_length_lst, key=lambda x: (len(x), x))
    
    return sorted_lst