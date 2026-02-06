def largest_smallest_integers(lst):
    neg_max = None
    pos_min = None
    for x in lst:
        try:
            # compare numerically; ignore non-numeric by catching TypeError
            if x < 0:
                if neg_max is None or x > neg_max:
                    neg_max = x
            elif x > 0:
                if pos_min is None or x < pos_min:
                    pos_min = x
        except TypeError:
            continue
    return (neg_max, pos_min)