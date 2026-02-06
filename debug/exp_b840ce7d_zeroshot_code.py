def is_sorted(lst):
    from collections import Counter
    if len(lst) <= 1:
        return True
    counts = Counter(lst)
    if any(c > 2 for c in counts.values()):
        return False
    for a, b in zip(lst, lst[1:]):
        if a > b:
            return False
    return True