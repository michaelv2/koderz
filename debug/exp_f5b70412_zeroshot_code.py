def generate_integers(a, b):
    """
    Given two integers a and b, return the even digits between a and b (inclusive),
    in ascending order.
    """
    lo, hi = min(a, b), max(a, b)
    even_digits = [0, 2, 4, 6, 8]
    return [d for d in even_digits if lo <= d <= hi]