def next_smallest(lst):
    unique_sorted = sorted(set(lst))
    if len(unique_sorted) < 2:
        return None
    return unique_sorted[1]