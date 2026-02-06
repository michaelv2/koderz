def max_fill(grid, capacity):
    total_drops = 0
    for row in grid:
        water_units = sum(row)
        drops_for_row = math.ceil(water_units / capacity)
        total_drops += drops_for_row
    return total_drops