def next_smallest(lst):
    """
    Return the 2nd smallest distinct element of the list, or None if it doesn't exist.
    """
    uniq = set(lst)
    if len(uniq) < 2:
        return None
    return sorted(uniq)[1]