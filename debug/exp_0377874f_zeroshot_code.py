def is_sorted(lst):
    # Check for duplicates
    if len(set(lst)) != len(lst):
        return False
    
    # Check if list is sorted
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))