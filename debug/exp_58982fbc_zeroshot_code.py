def generate_integers(a, b):
    """
    Given two positive integers a and b, return the even digits between a
    and b, in ascending order.
    """
    lo, hi = (a, b) if a <= b else (b, a)
    return [d for d in (0, 2, 4, 6, 8) if lo <= d <= hi]