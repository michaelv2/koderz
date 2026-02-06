def choose_num(x, y):
    import math
    if x > y:
        return -1
    hi = math.floor(y)
    if hi % 2 != 0:
        hi -= 1
    if hi < x:
        return -1
    return int(hi)