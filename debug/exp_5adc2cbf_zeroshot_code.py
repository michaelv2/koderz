import math

def poly(xs: list, x: float):
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[1] * x^2 + .... xs[n] * x^n
    """
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])


def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero find x such that poly(x) = 0.
    find_zero returns only only zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non zero coefficient as it guarantees
    a solution.
    """
    
    # Compute derivative coefficients
    # If f(x) = xs[0] + xs[1]*x + xs[2]*x^2 + ...
    # then f'(x) = xs[1] + 2*xs[2]*x + 3*xs[3]*x^2 + ...
    derivative_xs = [i * xs[i] for i in range(1, len(xs))]
    
    # Helper function to evaluate derivative
    def poly_derivative(x):
        return sum([coeff * math.pow(x, i) for i, coeff in enumerate(derivative_xs)])
    
    # Start with initial guess
    x = 0.0
    
    # Newton-Raphson method
    for _ in range(100):  # Maximum iterations
        fx = poly(xs, x)
        fpx = poly_derivative(x)
        
        # Avoid division by zero
        if abs(fpx) < 1e-10:
            break
        
        x_new = x - fx / fpx
        
        # Check for convergence
        if abs(x_new - x) < 1e-10:
            break
        
        x = x_new
    
    return x