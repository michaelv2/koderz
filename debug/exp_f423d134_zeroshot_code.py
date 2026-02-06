def max_element(l: list):
    if not l:
        raise ValueError("max_element() arg is an empty sequence")
    m = l[0]
    for x in l[1:]:
        if x > m:
            m = x
    return m