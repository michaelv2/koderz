def sort_third(l: list):
    idxs = [i for i in range(len(l)) if i % 3 == 0]
    vals = [l[i] for i in idxs]
    vals.sort()
    res = list(l)
    for j, i in enumerate(idxs):
        res[i] = vals[j]
    return res