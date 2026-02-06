def next_smallest(lst):
    """
    Return the 2nd smallest distinct element of the list, or None if not present.
    """
    unique = sorted(set(lst))
    return unique[1] if len(unique) >= 2 else None