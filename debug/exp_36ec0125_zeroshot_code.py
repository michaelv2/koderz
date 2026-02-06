def is_sorted(lst):
    from collections import Counter
    if any(v > 2 for v in Counter(lst).values()):
        return False
    return all(lst[i] <= lst[i+1] for i in range(len(lst)-1))