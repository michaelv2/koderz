def choose_num(x, y):
    import math
    if x > y:
        return -1
    max_floor = math.floor(y)
    if max_floor % 2 == 0:
        candidate = max_floor
    else:
        candidate = max_floor - 1
    if candidate >= x:
        return int(candidate)
    return -1