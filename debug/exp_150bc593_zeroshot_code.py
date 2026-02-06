def get_row(lst, x):
    coordinates = []
    
    # Find all occurrences of x
    for row_idx, row in enumerate(lst):
        for col_idx, val in enumerate(row):
            if val == x:
                coordinates.append((row_idx, col_idx))
    
    # Sort by row ascending, then by column descending within each row
    coordinates.sort(key=lambda coord: (coord[0], -coord[1]))
    
    return coordinates