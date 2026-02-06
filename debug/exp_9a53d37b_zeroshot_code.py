def find_max(words):
    if not words:
        return ""
    best = words[0]
    best_unique = len(set(best))
    for w in words[1:]:
        uniq = len(set(w))
        if uniq > best_unique:
            best_unique = uniq
            best = w
        elif uniq == best_unique and w < best:
            best = w
    return best