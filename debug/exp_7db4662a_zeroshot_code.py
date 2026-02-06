def derivative(xs: list):
    """Return the derivative coefficients of a polynomial represented by xs.
    xs[i] is the coefficient for x^i. The derivative coefficients are i * xs[i] for i >= 1.
    """
    return [i * xs[i] for i in range(1, len(xs))]