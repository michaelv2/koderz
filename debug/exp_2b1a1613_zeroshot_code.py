def largest_smallest_integers(lst):
    '''
    Create a function that returns a tuple (a, b), where 'a' is
    the largest of negative integers, and 'b' is the smallest
    of positive integers in a list.
    If there is no negative or positive integers, return them as None.
    '''
    neg_max = None
    pos_min = None
    for x in lst:
        if x < 0:
            if neg_max is None or x > neg_max:
                neg_max = x
        elif x > 0:
            if pos_min is None or x < pos_min:
                pos_min = x
    return (neg_max, pos_min)