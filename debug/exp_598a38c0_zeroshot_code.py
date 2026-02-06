def search(lst):
    cnt = {}
    for x in lst:
        cnt[x] = cnt.get(x, 0) + 1
    res = -1
    for k, v in cnt.items():
        if k > 0 and v >= k and k > res:
            res = k
    return res