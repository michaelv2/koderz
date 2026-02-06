def derivative(xs: list):
    """xs represents coefficients of a polynomial:
    xs[0] + xs[1]*x + xs[2]*x^2 + ...
    Return the derivative coefficients in the same form."""
    return [i * xs[i] for i in range(1, len(xs))]