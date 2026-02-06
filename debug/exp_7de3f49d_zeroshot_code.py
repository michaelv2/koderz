from any cell, and in each step you can move to any of the neighbor cells,

def minPath(grid, k):
    n = len(grid)
    # locate the position of value 1
    r, c = None, None
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1:
                r, c = i, j
                break
        if r is not None:
            break

    path = [1] if k >= 1 else []
    if k <= 1:
        return path

    for _ in range(k - 1):
        best_val = None
        best_r, best_c = None, None
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                v = grid[nr][nc]
                if best_val is None or v < best_val:
                    best_val = v
                    best_r, best_c = nr, nc
        r, c = best_r, best_c
        path.append(best_val)

    return path