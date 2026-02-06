def choose_num(x, y):
    if x > y:
        return -1
    candidate = y if y % 2 == 0 else y - 1
    if candidate < x:
        return -1
    return candidate