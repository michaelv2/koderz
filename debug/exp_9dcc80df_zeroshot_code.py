def total_match(lst1, lst2):
    # Calculate total number of characters in each list
    total_chars1 = sum(len(s) for s in lst1)
    total_chars2 = sum(len(s) for s in lst2)
    
    # Return the list with fewer total characters, or lst1 if equal
    if total_chars1 <= total_chars2:
        return lst1
    else:
        return lst2