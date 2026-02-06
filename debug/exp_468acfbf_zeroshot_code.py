from any cell, and in each step you can move to any of the neighbor cells,

def minPath(grid, k):
    if not grid or not grid[0] or k <= 0:
        return []
    
    n = len(grid)
    if k == 1:
        # Find minimum value in grid
        min_val = float('inf')
        for i in range(n):
            for j in range(n):
                min_val = min(min_val, grid[i][j])
        return [min_val]
    
    # Directions: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def dfs(x, y, path, remaining):
        if remaining == 0:
            return path[:]
        
        # Try all four directions
        min_val = float('inf')
        best_path = None
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n:
                # Check if this cell value can lead to a better path
                if grid[nx][ny] < min_val:
                    min_val = grid[nx][ny]
                    # Continue DFS
                    path.append(grid[nx][ny])
                    result = dfs(nx, ny, path, remaining - 1)
                    path.pop()
                    if result:
                        if best_path is None or result < best_path:
                            best_path = result
        
        return best_path
    
    # Try starting from each cell
    min_path = None
    
    for i in range(n):
        for j in range(n):
            # Start with current cell value
            path = [grid[i][j]]
            # DFS from this cell
            result = dfs(i, j, path, k - 1)
            if result:
                if min_path is None or result < min_path:
                    min_path = result
    
    return min_path if min_path else []