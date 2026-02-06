def minPath(grid, k):
    n = len(grid)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    visited = [[False] * n for _ in range(n)]
    path = []
    min_path = None

    def dfs(x, y, remaining):
        nonlocal min_path
        if remaining == 0:
            if not min_path or path < min_path:
                min_path = list(path)
            return
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and not visited[nx][ny]:
                path.append(grid[nx][ny])
                visited[nx][ny] = True
                dfs(nx, ny, remaining - 1)
                visited[nx][ny] = False
                path.pop()

    for i in range(n):
        for j in range(n):
            path.append(grid[i][j])
            visited[i][j] = True
            dfs(i, j, k - 1)
            visited[i][j] = False
            path.pop()
    return min_path