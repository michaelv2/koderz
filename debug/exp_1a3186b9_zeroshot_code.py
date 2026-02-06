def get_row(lst, x):
    coordinates = []
    
    for i, row in enumerate(lst):
        for j, element in enumerate(row):
            if element == x:
                coordinates.append((i, j))
    
    # Sort coordinates by row ascending and then by column descending
    sorted_coordinates = sorted(coordinates, key=lambda coord: (coord[0], -coord[1]))
    
    return sorted_coordinates