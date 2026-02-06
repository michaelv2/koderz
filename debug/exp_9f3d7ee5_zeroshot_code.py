def max_fill(grid, capacity):
    import math
    total_buckets = 0
    
    # For each well (row)
    for well in grid:
        # Count total water units in this well
        water_units = sum(well)
        # Calculate buckets needed (round up)
        buckets_needed = math.ceil(water_units / capacity)
        total_buckets += buckets_needed
    
    return total_buckets