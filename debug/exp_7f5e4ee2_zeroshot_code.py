def search(lst):
    '''
    You are given a non-empty list of positive integers. Return the greatest integer that is greater than 
    zero, and has a frequency greater than or equal to the value of the integer itself. 
    The frequency of an integer is the number of times it appears in the list.
    If no such a value exist, return -1.
    '''
    freq = {}
    for x in lst:
        freq[x] = freq.get(x, 0) + 1

    best = -1
    for val, cnt in freq.items():
        if val > 0 and cnt >= val and val > best:
            best = val
    return best