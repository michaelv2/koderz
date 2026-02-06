import math
from scipy import optimize

def poly(xs: list, x: float):
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])

def find_zero(xs: list):
    # The largest non-zero coefficient guarantees a solution.
    # We can use this to set the initial guess for the root finding algorithm.
    max_coeff = max([abs(x) for x in xs])
    
    # Use scipy's Newton's method to find the roots of the polynomial.
    return optimize.newton(lambda x: poly(xs, x), max_coeff)