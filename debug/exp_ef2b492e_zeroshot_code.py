def pairs_sum_to_zero(l):
    """
    Return True if there are two distinct elements in l that sum to zero.
    """
    seen = set()
    zero_count = 0
    for x in l:
        if x == 0:
            zero_count += 1
            if zero_count >= 2:
                return True
        if -x in seen:
            return True
        seen.add(x)
    return False