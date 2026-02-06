def unique_digits(x):
    """Given a list of positive integers x, return a sorted list of all elements that have no even digit."""
    return sorted(n for n in x if all(ch in "13579" for ch in str(n)))