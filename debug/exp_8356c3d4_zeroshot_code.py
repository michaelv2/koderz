def cycpattern_check(a, b):
    """
    Return True if the second word or any rotation of it is a substring of the first word.
    """
    if not b:
        return True  # empty string is a substring of any string
    for i in range(len(b)):
        rotated = b[i:] + b[:i]
        if rotated in a:
            return True
    return False