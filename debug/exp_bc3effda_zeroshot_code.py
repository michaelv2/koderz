def unique_digits(x):
    """Given a list of positive integers x. return a sorted list of all 
    elements that hasn't any even digit.
    """
    res = []
    for n in x:
        s = str(n)
        if all((ord(ch) - 48) % 2 == 1 for ch in s):
            res.append(n)
    return sorted(res)