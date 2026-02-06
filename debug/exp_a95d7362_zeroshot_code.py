def is_sorted(lst):
    """
    Given a list of numbers, return whether or not they are sorted
    in ascending order. If list has more than 1 duplicate of the same
    number, return False. Assume no negative numbers and only integers.
    """
    if len(lst) <= 1:
        return True

    prev = lst[0]
    dup_count = 1  # count of current number appearances

    for x in lst[1:]:
        if x < prev:
            return False
        if x == prev:
            dup_count += 1
            if dup_count > 2:
                return False
        else:
            prev = x
            dup_count = 1

    return True