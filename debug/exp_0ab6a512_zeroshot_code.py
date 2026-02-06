from collections import Counter

def search(lst):
    cnt = Counter(lst)
    candidates = [num for num, c in cnt.items() if num > 0 and c >= num]
    return max(candidates) if candidates else -1