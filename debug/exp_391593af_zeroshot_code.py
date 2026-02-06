def get_row(lst, x):
    result = []
    for i, row in enumerate(lst):
        if not row:
            continue
        cols = [j for j, val in enumerate(row) if val == x]
        if cols:
            cols.sort(reverse=True)
            for j in cols:
                result.append((i, j))
    return result