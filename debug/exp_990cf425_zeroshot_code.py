def unique_digits(x):
    """Given a list of positive integers x. return a sorted list of all 
    elements that hasn't any even digit.
    """
    result = []
    for n in x:
        s = str(n)
        # handle possible negative sign defensively
        if s.startswith('-'):
            s = s[1:]
        # check that every digit is odd
        if all((ord(ch) - ord('0')) % 2 == 1 for ch in s):
            result.append(n)
    return sorted(result)