def is_sorted(lst):
    if not lst:
        return True
    run_len = 1
    prev = lst[0]
    for x in lst[1:]:
        if x < prev:
            return False
        if x == prev:
            run_len += 1
            if run_len > 2:
                return False
        else:
            prev = x
            run_len = 1
    return True