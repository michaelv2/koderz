import math

def max_fill(grid, capacity):
    total_operations = 0
    for row in grid:
        water_units = sum(row)
        operations = (water_units + capacity - 1) // capacity
        total_operations += operations
    return total_operations