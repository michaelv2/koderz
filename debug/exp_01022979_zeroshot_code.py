import math

def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero find x such that poly(x) = 0.
    find_zero returns only one zero point, even if there are many.
    It operates on polynomials with an odd degree (even number of coefficients)
    to guarantee a real root exists.
    """
    if xs is None or len(xs) == 0:
        raise ValueError("coefficient list is empty")
    # Work with floats for numerics
    coeffs = [float(c) for c in xs]

    # Remove trailing zeros to ensure the leading coefficient is non-zero
    while len(coeffs) > 1 and coeffs[-1] == 0.0:
        coeffs.pop()

    # If all coefficients were zero (degenerate), root is undefined; return 0.0
    if all(c == 0.0 for c in coeffs):
        return 0.0

    # Helper to evaluate polynomial using given poly function
    def f(x):
        return poly(coeffs, x)

    # Initialize interval where a sign change occurs
    a, b = -1.0, 1.0
    fa, fb = f(a), f(b)

    # Expand interval until a sign change is found
    r = 1.0
    iter_expand = 0
    while fa * fb > 0:
        r *= 2.0
        a, b = -r, r
        fa, fb = f(a), f(b)
        iter_expand += 1
        if iter_expand > 60:
            # Fallback: use a simple Newton's method starting at 0
            x = 0.0
            for _ in range(1000):
                val = f(x)
                # Compute derivative of polynomial at x
                d = 0.0
                for i in range(1, len(coeffs)):
                    d += i * coeffs[i] * (x ** (i - 1))
                if d == 0:
                    break
                x_new = x - val / d
                if abs(x_new - x) < 1e-12:
                    x = x_new
                    break
                x = x_new
            return x

    # Bisection to refine the root
    left, right = a, b
    f_left, f_right = fa, fb
    for _ in range(200):
        mid = (left + right) / 2.0
        f_mid = f(mid)
        if abs(f_mid) < 1e-12:
            return mid
        if f_left * f_mid <= 0:
            right = mid
            f_right = f_mid
        else:
            left = mid
            f_left = f_mid
    return (left + right) / 2.0