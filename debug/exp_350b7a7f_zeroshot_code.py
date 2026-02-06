def is_sorted(lst):
    if len(lst) <= 1:
        return True
    prev = lst[0]
    counts = {prev: 1}
    for x in lst[1:]:
        if x < prev:
            return False
        counts[x] = counts.get(x, 0) + 1
        if counts[x] > 2:
            return False
        prev = x
    return True