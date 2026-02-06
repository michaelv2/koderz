def next_smallest(lst):
    lst = list(set(lst))
    if len(lst) < 2:
        return None
    else:
        lst.sort()
        return lst[1]