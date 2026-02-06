import math

def max_fill(grid, capacity):
    total_buckets = 0
    for row in grid:
        water_units = sum(row)
        buckets_needed = math.ceil(water_units / capacity)
        total_buckets += buckets_needed
    return total_buckets