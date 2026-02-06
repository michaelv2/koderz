def largest_smallest_integers(lst):
    max_neg = None  # largest among negative numbers
    min_pos = None  # smallest among positive numbers

    for x in lst:
        if x < 0:
            if max_neg is None or x > max_neg:
                max_neg = x
        elif x > 0:
            if min_pos is None or x < min_pos:
                min_pos = x

    return (max_neg, min_pos)