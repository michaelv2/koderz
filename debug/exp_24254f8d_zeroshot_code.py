def sort_even(l: list):
    """This function takes a list l and returns a list l' such that
    l' is identical to l in the odd indicies, while its values at the even indicies are equal
    to the values of the even indicies of l, but sorted.
    >>> sort_even([1, 2, 3])
    [1, 2, 3]
    >>> sort_even([5, 6, 3, 4])
    [3, 6, 5, 4]
    """
    # Extract elements at even indices
    even_elements = [l[i] for i in range(0, len(l), 2)]
    
    # Sort them
    even_elements.sort()
    
    # Create result list
    result = l.copy()
    
    # Put sorted even elements back at even indices
    for i, val in enumerate(even_elements):
        result[2 * i] = val
    
    return result