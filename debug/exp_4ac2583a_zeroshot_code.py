def choose_num(x, y):
    import math
    # If range invalid
    if x > y:
        return -1
    # Largest integer <= y
    fy = math.floor(y)
    # Make it even
    if fy % 2 != 0:
        fy -= 1
    # Check if this even integer is within [x, y]
    if fy >= x:
        return fy
    return -1