def common(l1: list, l2: list):
    """Return sorted unique common elements for two lists."""
    # Convert both lists to sets to remove duplicates and find intersection
    set1 = set(l1)
    set2 = set(l2)
    common_elements = set1.intersection(set2)
    
    # Convert the set back to a list and sort it
    return sorted(list(common_elements))