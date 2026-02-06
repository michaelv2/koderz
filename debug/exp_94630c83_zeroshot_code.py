def get_row(lst, x):
    coordinates = []
    for i, row in enumerate(lst):
        for j, value in enumerate(row):
            if value == x:
                coordinates.append((i, j))
    # Sort by row index ascending, then by column index descending
    coordinates.sort(key=lambda coord: (coord[0], -coord[1]))
    return coordinates