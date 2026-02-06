def find_max(words):
    """Return the word with the maximum number of unique characters.
    If multiple words tie, return the lexicographically smallest one.
    """
    if not words:
        return ""
    max_unique = max(len(set(w)) for w in words)
    candidates = [w for w in words if len(set(w)) == max_unique]
    return min(candidates)