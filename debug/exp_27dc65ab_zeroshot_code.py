def next_smallest(lst):
    """
    Return the second smallest distinct element in lst.
    If there are fewer than two distinct elements, return None.
    """
    uniq = set(lst)
    if len(uniq) < 2:
        return None
    return sorted(uniq)[1]