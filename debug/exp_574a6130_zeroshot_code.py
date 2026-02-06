def sorted_list_sum(lst):
    """Filter out strings with odd lengths and return the list sorted by length then alphabetically."""
    return sorted((s for s in lst if len(s) % 2 == 0), key=lambda s: (len(s), s))