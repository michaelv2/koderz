def next_smallest(lst):
    unique_elements = set(lst)
    if len(unique_elements) < 2:
        return None
    sorted_unique_elements = sorted(unique_elements)
    return sorted_unique_elements[1]