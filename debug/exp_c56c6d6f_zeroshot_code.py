def minPath(grid, k):
    """
    Given the grid and k, return the lexicographically smallest sequence of values
    along a path of length k (visiting exactly k cells), moving only to edge-sharing neighbors.
    """
    n = len(grid)
    # find position of the minimal value (values are unique)
    min_val = None
    r = c = 0
    for i in range(n):
        for j in range(n):
            v = grid[i][j]
            if min_val is None or v < min_val:
                min_val = v
                r, c = i, j
    path = [min_val]
    # directions: up, down, left, right
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    for _ in range(k-1):
        best_val = None
        best_pos = (r, c)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                val = grid[nr][nc]
                if best_val is None or val < best_val:
                    best_val = val
                    best_pos = (nr, nc)
        # move to best neighbor (there is always at least one neighbor since n>=2)
        r, c = best_pos
        path.append(grid[r][c])
    return path