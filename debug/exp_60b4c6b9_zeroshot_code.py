def search(lst):
    from collections import Counter
    freq = Counter(lst)
    candidates = [k for k, v in freq.items() if k > 0 and v >= k]
    return max(candidates) if candidates else -1