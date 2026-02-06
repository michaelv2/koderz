def max_fill(grid, capacity):
    total = 0
    for row in grid:
        k = sum(row)
        total += (k + capacity - 1) // capacity
    return total