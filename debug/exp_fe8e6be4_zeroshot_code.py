def sort_even(l: list):
    """This function takes a list l and returns a list l' such that
    l' is identical to l in the odd indicies, while its values at the even indicies are equal
    to the values of the even indicies of l, but sorted.
    """
    res = list(l)
    even_vals = sorted(res[0::2])
    idx = 0
    for i in range(0, len(res), 2):
        res[i] = even_vals[idx]
        idx += 1
    return res