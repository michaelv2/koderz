def sort_third(l: list):
    """This function takes a list l and returns a list l' such that
    l' is identical to l in the indicies that are not divisible by three, while its values at the indicies that are divisible by three are equal
    to the values of the corresponding indicies of l, but sorted.
    """
    res = list(l)
    vals = [res[i] for i in range(0, len(res), 3)]
    vals.sort()
    vi = 0
    for i in range(0, len(res), 3):
        res[i] = vals[vi]
        vi += 1
    return res