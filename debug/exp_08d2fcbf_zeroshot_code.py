def median(l: list):
    """Return median of elements in the list l."""
    sorted_l = sorted(l)
    n = len(sorted_l)
    
    if n % 2 == 1:
        # Odd number of elements
        return sorted_l[n // 2]
    else:
        # Even number of elements
        return (sorted_l[n // 2 - 1] + sorted_l[n // 2]) / 2