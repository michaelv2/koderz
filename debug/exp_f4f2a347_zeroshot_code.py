def common(l1: list, l2: list):
    # Convert both lists to sets for efficient intersection operation
    set_l1 = set(l1)
    set_l2 = set(l2)
    
    # Find the intersection of two sets and convert it back to a list
    common_elements = list(set_l1 & set_l2)
    
    # Sort the list in ascending order
    common_elements.sort()
    
    return common_elements