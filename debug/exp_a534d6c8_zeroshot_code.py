def unique_digits(x):
    """Given a list of positive integers x. return a sorted list of all 
    elements that hasn't any even digit.
    """
    res = []
    for n in x:
        s = str(n)
        # consider only digit characters (ignore sign if any)
        digits = [ch for ch in s if ch.isdigit()]
        if digits and all((int(ch) % 2 == 1) for ch in digits):
            res.append(n)
    return sorted(res)