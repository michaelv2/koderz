def sort_third(l: list):
    vals = [l[i] for i in range(len(l)) if i % 3 == 0]
    vals.sort()
    res = list(l)
    it = iter(vals)
    for i in range(len(res)):
        if i % 3 == 0:
            res[i] = next(it)
    return res