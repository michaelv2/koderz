def pluck(arr):
    best = None
    best_i = None
    for i, v in enumerate(arr):
        if v % 2 == 0:
            if best is None or v < best:
                best = v
                best_i = i
    return [] if best is None else [best, best_i]