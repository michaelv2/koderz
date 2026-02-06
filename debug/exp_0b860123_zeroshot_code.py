def by_length(arr):
    if not arr:
        return []
    names = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    # Keep only numbers between 1 and 9 inclusive
    filtered = [x for x in arr if 1 <= x <= 9]
    # Sort ascending, then reverse to get descending
    filtered.sort()
    filtered.reverse()
    # Map to names
    return [names[x] for x in filtered]