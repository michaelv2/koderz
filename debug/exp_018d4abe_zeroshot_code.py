def strange_sort_list(lst):
    arr = sorted(lst)
    res = []
    i, j = 0, len(arr) - 1
    while i <= j:
        res.append(arr[i])
        i += 1
        if i <= j:
            res.append(arr[j])
            j -= 1
    return res