def unique(l: list):
    """Return sorted unique elements in a list
    >>> unique([5, 3, 5, 2, 3, 3, 9, 0, 123])
    [0, 2, 3, 5, 9, 123]
    """
    try:
        return sorted(set(l))
    except TypeError:
        # Elements may be unhashable; deduplicate preserving insertion order
        seen = []
        for x in l:
            if x not in seen:
                seen.append(x)
        try:
            return sorted(seen)
        except TypeError:
            # Elements not comparable; return in original first-seen order
            return seen