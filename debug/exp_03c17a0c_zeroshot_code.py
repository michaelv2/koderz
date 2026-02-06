def search(lst):
    from collections import Counter
    freq = Counter(lst)
    best = -1
    for x, f in freq.items():
        if x > 0 and f >= x:
            if x > best:
                best = x
    return best