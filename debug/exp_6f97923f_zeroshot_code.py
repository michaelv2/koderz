def add(lst):
    """Given a non-empty list of integers lst. add the even elements that are at odd indices."""
    return sum(v for i, v in enumerate(lst) if i % 2 == 1 and v % 2 == 0)