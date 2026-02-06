def get_row(lst, x):
    res = []
    for i, row in enumerate(lst):
        cols = [j for j, val in enumerate(row) if val == x]
        cols.sort(reverse=True)
        for c in cols:
            res.append((i, c))
    return res