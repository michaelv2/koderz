def is_sorted(lst):
    # Check if list is sorted in ascending order
    for i in range(len(lst) - 1):
        if lst[i] > lst[i + 1]:
            return False
    
    # Check if any number has more than 1 duplicate (appears more than twice)
    from collections import Counter
    counts = Counter(lst)
    for count in counts.values():
        if count > 2:
            return False
    
    return True