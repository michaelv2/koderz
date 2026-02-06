def find_max(words):
    if not words:
        return ""
    best = None
    best_count = -1
    for w in words:
        cnt = len(set(w))
        if cnt > best_count:
            best_count = cnt
            best = w
        elif cnt == best_count:
            if w < best:
                best = w
    return best