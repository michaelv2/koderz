def minPath(grid, k):
    n = len(grid)
    # locate the cell containing 1
    start = None
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1:
                start = (i, j)
                break
        if start is not None:
            break

    if start is None or k <= 0:
        return []

    r, c = start
    path = [1]

    if k == 1:
        return path

    # four-neighborhoods
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for _ in range(1, k):
        best_val = None
        best_pos = None
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                v = grid[nr][nc]
                if best_val is None or v < best_val:
                    best_val = v
                    best_pos = (nr, nc)
        r, c = best_pos
        path.append(best_val)

    return path