from any cell, and in each step you can move to any of the neighbor cells,

def minPath(grid, k):
    n = len(grid)
    
    # Find position of value 1 (smallest value, best starting point for lexicographic comparison)
    start_pos = None
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1:
                start_pos = (i, j)
                break
        if start_pos:
            break
    
    # Best path found so far
    best_path = None
    
    def dfs(i, j, path):
        nonlocal best_path
        
        # Base case: path length reached k
        if len(path) == k:
            if best_path is None or path < best_path:
                best_path = path[:]
            return
        
        # Pruning: if current path is already worse than best found, stop
        if best_path is not None and path >= best_path[:len(path)]:
            return
        
        # Try all 4 neighbors
        neighbors = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        for ni, nj in neighbors:
            if 0 <= ni < n and 0 <= nj < n:
                path.append(grid[ni][nj])
                dfs(ni, nj, path)
                path.pop()
    
    # Start DFS from position of 1
    dfs(start_pos[0], start_pos[1], [grid[start_pos[0]][start_pos[1]]])
    
    return best_path