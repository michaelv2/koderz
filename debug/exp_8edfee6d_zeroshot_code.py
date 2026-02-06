def is_sorted(lst):
    '''
    Given a list of numbers, return whether or not they are sorted
    in ascending order. If list has more than 1 duplicate of the same
    number, return False. Assume no negative numbers and only integers.
    '''
    if not lst:
        return True
    # Check non-decreasing (ascending allowing equals)
    for a, b in zip(lst, lst[1:]):
        if a > b:
            return False
    # Check no number appears more than twice
    counts = {}
    for x in lst:
        counts[x] = counts.get(x, 0) + 1
        if counts[x] > 2:
            return False
    return True