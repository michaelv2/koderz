import math

def poly(xs: list, x: float):
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[2] * x^2 + .... xs[n] * x^n
    """
    return sum(coeff * (x ** i) for i, coeff in enumerate(xs))

def poly_derivative(xs: list, x: float):
    """
    Evaluates the derivative of polynomial with coefficients xs at point x.
    """
    return sum(i * coeff * (x ** (i - 1)) for i, coeff in enumerate(xs) if i > 0)

def find_zero(xs: list):
    """ 
    xs are coefficients of a polynomial.
    find_zero finds x such that poly(x) = 0.
    find_zero returns only one zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non zero coefficient as it guarantees a solution.
    """
    # Initial guess can be 0 or any other value
    x = 0.0
    tolerance = 1e-7
    max_iterations = 1000
    
    for _ in range(max_iterations):
        fx = poly(xs, x)
        fpx = poly_derivative(xs, x)
        
        if abs(fx) < tolerance:
            return x
        
        if fpx == 0:
            raise ValueError("Derivative is zero. No solution found.")
        
        x_new = x - fx / fpx
        if abs(x_new - x) < tolerance:
            return x_new
        
        x = x_new
    
    raise RuntimeError("Failed to converge to a solution.")