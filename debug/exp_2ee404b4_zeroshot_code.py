def find_max(words):
    max_unique = max(len(set(word)) for word in words)
    candidates = [word for word in words if len(set(word)) == max_unique]
    return min(candidates)