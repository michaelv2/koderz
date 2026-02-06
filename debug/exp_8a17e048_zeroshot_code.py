import math

def poly(xs: list, x: float) -> float:
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[2] * x^2 + .... xs[n] * x^n
    """
    return sum(coeff * math.pow(x, i) for i, coeff in enumerate(xs))

def find_zero(xs: list) -> float:
    """ 
    Finds a real zero of the polynomial with coefficients xs.
    Returns a single floating-point number r such that poly(r) == 0 within tolerance.
    """
    # Define initial interval and tolerance
    a, b = -100.0, 100.0
    tol = 1e-7
    
    # Ensure the polynomial changes sign over the interval [a, b]
    while poly(xs, a) * poly(xs, b) > 0:
        a *= 2
        b *= 2
    
    # Bisection method
    while (b - a) / 2.0 > tol:
        m = (a + b) / 2.0
        if poly(xs, m) == 0:
            return m
        elif poly(xs, a) * poly(xs, m) < 0:
            b = m
        else:
            a = m
    
    return (a + b) / 2.0