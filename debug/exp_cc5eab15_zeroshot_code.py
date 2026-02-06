import math

def max_fill(grid, capacity):
    total = 0
    for row in grid:
        units = sum(row)
        if units:
            total += (units + capacity - 1) // capacity
    return total