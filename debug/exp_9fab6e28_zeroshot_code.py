def strange_sort_list(lst):
    if not lst:
        return []
    a = sorted(lst)
    i, j = 0, len(a) - 1
    res = []
    take_min = True
    while i <= j:
        if take_min:
            res.append(a[i])
            i += 1
        else:
            res.append(a[j])
            j -= 1
        take_min = not take_min
    return res