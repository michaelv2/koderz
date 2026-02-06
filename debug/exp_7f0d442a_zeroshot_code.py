def by_length(arr):
    """
    Filter numbers 1..9, sort ascending, then reverse to descending,
    and replace each digit with its corresponding English name.
    """
    names = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    filtered = [n for n in arr if isinstance(n, int) and 1 <= n <= 9]
    if not filtered:
        return []
    filtered.sort()
    filtered.reverse()
    return [names[n] for n in filtered]