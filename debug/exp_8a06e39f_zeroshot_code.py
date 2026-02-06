def max_fill(grid, capacity):
    import math
    
    # Count total water units (1s) in the grid
    total_water = 0
    for row in grid:
        total_water += sum(row)
    
    # If no water, no operations needed
    if total_water == 0:
        return 0
    
    # Calculate number of bucket operations needed (round up)
    return math.ceil(total_water / capacity)