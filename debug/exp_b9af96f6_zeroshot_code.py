def sorted_list_sum(lst):
    """Filter out strings with odd lengths and return the remaining strings
    sorted by increasing length, and alphabetically for ties."""
    filtered = [s for s in lst if len(s) % 2 == 0]
    filtered.sort(key=lambda x: (len(x), x))
    return filtered