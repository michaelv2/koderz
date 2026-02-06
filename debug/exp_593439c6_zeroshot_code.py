def max_fill(grid, capacity):
    def fill_bucket(row, col):
        if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]) or grid[row][col] == 0:
            return 0
        water = 1
        grid[row][col] = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = row + dx, col + dy
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]):
                water += fill_bucket(nx, ny)
        return min(water, capacity)

    buckets = 0
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == 1:
                buckets += fill_bucket(i, j)
    return buckets