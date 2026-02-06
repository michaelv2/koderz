def choose_num(x, y):
    """This function takes two positive numbers x and y and returns the
    biggest even integer number that is in the range [x, y] inclusive. If 
    there's no such number, then the function should return -1.

    For example:
    choose_num(12, 15) = 14
    choose_num(13, 12) = -1
    """
    if x > y:
        return -1
    
    # Start from y and go backwards to find the largest even number
    if y % 2 == 0:
        # y is even, so it's our answer
        return y
    else:
        # y is odd, so check if y-1 is within range
        if y - 1 >= x:
            return y - 1
        else:
            return -1