def max_element(l: list):
    """Return maximum element in the list."""
    if not l:
        raise ValueError("max_element() arg is an empty list")
    m = l[0]
    for x in l[1:]:
        if x > m:
            m = x
    return m