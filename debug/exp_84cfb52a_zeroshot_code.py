def simplify(x, n):
    """Return True if the product of two fractions x and n is an integer.
    x and n are strings in the form 'numerator/denominator' with positive integers."""
    a, b = map(int, x.strip().split('/'))
    c, d = map(int, n.strip().split('/'))
    return (a * c) % (b * d) == 0