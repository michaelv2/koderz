def sorted_list_sum(lst):
    """Remove strings with odd length and return the remaining strings sorted by length, then alphabetically."""
    filtered = [s for s in lst if len(s) % 2 == 0]
    return sorted(filtered, key=lambda x: (len(x), x))