def max_fill(grid, capacity):
    total = 0
    for row in grid:
        ones = sum(row)
        if ones:
            total += (ones + capacity - 1) // capacity
    return total