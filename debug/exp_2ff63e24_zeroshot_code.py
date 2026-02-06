def next_smallest(lst):
    unique_vals = set(lst)
    if len(unique_vals) < 2:
        return None
    s = sorted(unique_vals)
    return s[1]