def get_row(lst, x):
    coordinates = []
    for i in range(len(lst)):
        for j in range(len(lst[i])):
            if lst[i][j] == x:
                coordinates.append((i, len(lst[i]) - 1 - j))
    coordinates.sort(key=lambda coord: (coord[0], -coord[1]))
    return coordinates