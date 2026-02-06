def strange_sort_list(lst):
    a = sorted(lst)
    res = []
    i, j = 0, len(a) - 1
    while i <= j:
        res.append(a[i])
        i += 1
        if i <= j:
            res.append(a[j])
            j -= 1
    return res