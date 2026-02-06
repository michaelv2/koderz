import math

def poly(xs: list, x: float):
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[2] * x^2 + .... xs[n] * x^n
    """
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])

def poly_derivative(xs: list, x: float):
    """
    Evaluates the derivative of the polynomial with coefficients xs at point x.
    """
    return sum([i * coeff * math.pow(x, i - 1) for i, coeff in enumerate(xs)][1:])

def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero finds x such that poly(x) = 0.
    find_zero returns only one zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non-zero coefficient as it guarantees a solution.
    """
    # Initial guess
    x = 0.0
    
    # Tolerance for convergence
    tolerance = 1e-6
    
    # Maximum number of iterations to prevent infinite loops
    max_iterations = 1000
    
    for _ in range(max_iterations):
        fx = poly(xs, x)
        fpx = poly_derivative(xs, x)
        
        if abs(fx) < tolerance:
            return round(x, 2)
        
        if fpx == 0:
            break
        
        x -= fx / fpx
    
    raise ValueError("Newton-Raphson method did not converge")