def minPath(grid, k):
    N = len(grid)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    def dfs(x, y, path):
        if len(path) == k:
            nonlocal min_path
            if min_path is None or path < min_path:
                min_path = path[:]
            return
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < N and 0 <= ny < N:
                path.append(grid[nx][ny])
                dfs(nx, ny, path)
                path.pop()
    
    min_path = None
    for i in range(N):
        for j in range(N):
            dfs(i, j, [grid[i][j]])
    
    return min_path