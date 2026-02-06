def sort_third(l: list):
    """Replaces elements at indices divisible by 3 with them sorted,
    leaving other positions unchanged."""
    res = list(l)
    indices = [i for i in range(len(l)) if i % 3 == 0]
    sorted_vals = sorted(res[i] for i in indices)
    for idx, i in enumerate(indices):
        res[i] = sorted_vals[idx]
    return res