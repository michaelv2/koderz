def sort_third(l: list):
    res = l[:]
    idx = [i for i in range(len(l)) if i % 3 == 0]
    vals = [l[i] for i in idx]
    vals.sort()
    for j, i in enumerate(idx):
        res[i] = vals[j]
    return res