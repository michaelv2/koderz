def unique_digits(x):
    """
    Given a list of positive integers, return a sorted list of those elements
    that contain only odd digits (i.e., no even digits among its decimal digits).
    """
    return sorted(n for n in x if all(int(d) % 2 == 1 for d in str(n)))