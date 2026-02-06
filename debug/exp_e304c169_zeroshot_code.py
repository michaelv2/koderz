def get_row(lst, x):
    """
    Return list of (row, column) tuples where value equals x.
    Rows sorted ascending; within each row, columns sorted descending.
    """
    result = []
    for i, row in enumerate(lst):
        cols = [j for j, val in enumerate(row) if val == x]
        cols.sort(reverse=True)
        for j in cols:
            result.append((i, j))
    return result