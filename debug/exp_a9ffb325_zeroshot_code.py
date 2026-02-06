def histogram(test):
    """Return a dictionary of the most frequent letter(s) in a space-separated string.

    - Input: a string containing space-separated lowercase letters.
    - Output: a dict mapping each letter that has the maximum frequency to its count.
    - If input is empty or contains no letters, return an empty dict.
    """
    if not test:
        return {}
    counts = {}
    for ch in test.split():
        counts[ch] = counts.get(ch, 0) + 1

    if not counts:
        return {}

    max_count = max(counts.values())
    return {ch: cnt for ch, cnt in counts.items() if cnt == max_count}