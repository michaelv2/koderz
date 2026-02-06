def histogram(test):
    """Given a string representing a space separated lowercase letters, return a dictionary
    of the letter with the most repetition and containing the corresponding count.
    If several letters have the same occurrence, return all of them.
    """
    if not test or not test.strip():
        return {}
    parts = test.split()
    from collections import Counter
    counts = Counter(parts)
    if not counts:
        return {}
    max_count = max(counts.values())
    return {k: v for k, v in counts.items() if v == max_count}