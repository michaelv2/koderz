def strange_sort_list(lst):
    if not lst:
        return []
    s = sorted(lst)
    res = []
    i, j = 0, len(s) - 1
    while i <= j:
        res.append(s[i])
        i += 1
        if i <= j:
            res.append(s[j])
            j -= 1
    return res