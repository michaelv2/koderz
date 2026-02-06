def sort_even(l: list):
    res = l[:]
    even_indices = range(0, len(l), 2)
    sorted_evens = sorted(l[i] for i in even_indices)
    for idx, i in enumerate(even_indices):
        res[i] = sorted_evens[idx]
    return res