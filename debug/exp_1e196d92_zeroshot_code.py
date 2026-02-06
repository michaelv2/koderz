def strange_sort_list(lst):
    a = sorted(lst)
    res = []
    left, right = 0, len(a) - 1
    take_min = True
    while left <= right:
        if take_min:
            res.append(a[left])
            left += 1
        else:
            res.append(a[right])
            right -= 1
        take_min = not take_min
    return res