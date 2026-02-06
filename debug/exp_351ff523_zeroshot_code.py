def sum_squares(lst):
    from math import ceil
    return sum(ceil(x) ** 2 for x in lst)