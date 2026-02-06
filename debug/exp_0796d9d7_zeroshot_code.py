import math

def poly(xs: list, x: float) -> float:
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[2] * x^2 + .... xs[n] * x^n
    """
    return sum(coeff * math.pow(x, i) for i, coeff in enumerate(xs))

def poly_derivative(xs: list, x: float) -> float:
    """
    Evaluates the derivative of polynomial with coefficients xs at point x.
    The derivative is given by:
    0 + xs[1] + 2 * xs[2] * x + ... + n * xs[n] * x^(n-1)
    """
    return sum(i * coeff * math.pow(x, i - 1) for i, coeff in enumerate(xs) if i > 0)

def find_zero(xs: list) -> float:
    """ 
    Finds x such that poly(x) = 0 using the Newton-Raphson method.
    xs are coefficients of a polynomial with an even number of coefficients.
    """
    # Initial guess can be set to 0 or any other reasonable value
    x = 0.0
    tolerance = 1e-7
    max_iterations = 1000
    
    for _ in range(max_iterations):
        fx = poly(xs, x)
        f_prime_x = poly_derivative(xs, x)
        
        if abs(f_prime_x) < tolerance:
            raise ValueError("Derivative near zero, no convergence possible.")
        
        # Newton-Raphson iteration
        x_new = x - fx / f_prime_x
        
        # Check for convergence
        if abs(x_new - x) < tolerance:
            return x_new
        
        x = x_new
    
    raise RuntimeError("Failed to converge to a solution.")