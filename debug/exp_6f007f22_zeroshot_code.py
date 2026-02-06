def median(l: list):
    """Return median of elements in the list l."""
    if not l:
        raise ValueError("List is empty")
    
    sorted_l = sorted(l)
    n = len(sorted_l)
    
    if n % 2 == 1:
        return sorted_l[n // 2]
    else:
        mid1, mid2 = sorted_l[n // 2 - 1], sorted_l[n // 2]
        return (mid1 + mid2) / 2