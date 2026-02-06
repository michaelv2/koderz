def is_sorted(lst):
    return lst == sorted(set(lst)) and len(lst) == len(set(lst))