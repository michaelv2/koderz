import math

def poly(xs: list, x: float):
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])

def find_zero(xs: list):
    # Initialize the interval [a, b]
    a = 0
    b = 1

    # Set the tolerance and maximum number of iterations
    tol = 1e-6
    max_iter = 1000

    # Check if f(a) and f(b) have opposite signs
    if poly(xs, a) * poly(xs, b) > 0:
        raise ValueError("The interval [a, b] does not contain a root.")

    # Perform the bisection method
    for _ in range(max_iter):
        c = (a + b) / 2
        if poly(xs, c) == 0 or abs(b - a) < tol:
            return c
        elif poly(xs, a) * poly(xs, c) < 0:
            b = c
        else:
            a = c

    raise ValueError("The method did not converge.")