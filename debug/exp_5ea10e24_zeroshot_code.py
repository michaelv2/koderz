def find_max(words):
    if not words:
        return ""
    best = None
    max_unique = -1
    for w in words:
        uniq = len(set(w))
        if uniq > max_unique:
            max_unique = uniq
            best = w
        elif uniq == max_unique:
            if best is None or w < best:
                best = w
    return best if best is not None else ""