def find_max(words):
    if not words:
        return ""
    max_unique = -1
    candidates = []
    for w in words:
        u = len(set(w))
        if u > max_unique:
            max_unique = u
            candidates = [w]
        elif u == max_unique:
            candidates.append(w)
    return min(candidates)