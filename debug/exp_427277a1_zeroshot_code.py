import math

def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero find x such that poly(x) = 0.
    find_zero returns only one zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non zero coefficient as it guarantees a solution.
    """
    if not isinstance(xs, list) or len(xs) == 0:
        raise ValueError("xs must be a non-empty list")
    # Work on a copy to avoid mutating input
    coeffs = xs[:]
    # Remove trailing zeros to determine the true degree
    while coeffs and coeffs[-1] == 0:
        coeffs.pop()
    if len(coeffs) == 0:
        return 0.0
    if len(coeffs) % 2 == 1:
        raise ValueError("xs must have an even number of coefficients after trimming trailing zeros")

    def f(t: float) -> float:
        return poly(coeffs, t)

    # Try to find a bracket [a, b] such that f(a) and f(b) have opposite signs
    a, b = -1.0, 1.0
    fa, fb = f(a), f(b)
    if fa == 0:
        return a
    if fb == 0:
        return b

    # Expand outward until a sign change is found (guaranteed for odd degree)
    R = 1.0
    while fa * fb > 0:
        R *= 2.0
        a, b = -R, R
        fa, fb = f(a), f(b)
        if fa == 0:
            return a
        if fb == 0:
            return b
        if R > 1e6:
            break  # safety

    left, right = a, b
    fl, fr = fa, fb

    # Bisection to refine the root
    for _ in range(200):
        mid = 0.5 * (left + right)
        fm = f(mid)
        if fm == 0:
            return mid
        if fl * fm < 0:
            right, fr = mid, fm
        else:
            left, fl = mid, fm
        if right - left < 1e-12:
            return 0.5 * (left + right)

    return 0.5 * (left + right)