import math

def find_zero(xs: list):
    """Find a real root of the polynomial with coefficients xs using bisection.
    Assumes len(xs) is even so the polynomial degree is odd (guaranteed real root).
    """
    if not xs:
        raise ValueError("Coefficient list xs must be non-empty")

    # Horner's method for polynomial evaluation
    def p(x):
        # evaluate xs[0] + xs[1]*x + ... + xs[n]*x^n
        # Horner: ((...x * x + xs[n-1]) * x + xs[n-2]) ... but we adapt for given order
        # Start from highest degree
        val = 0.0
        for coeff in reversed(xs):
            val = val * x + coeff
        return val

    # initial bounds
    a = -1.0
    b = 1.0
    fa = p(a)
    if fa == 0.0:
        return a
    fb = p(b)
    if fb == 0.0:
        return b

    # expand bounds until sign change or until limit
    max_expand = 100
    for _ in range(max_expand):
        if fa * fb < 0.0:
            break
        a *= 2.0
        b *= 2.0
        fa = p(a)
        if fa == 0.0:
            return a
        fb = p(b)
        if fb == 0.0:
            return b
    else:
        # as a fallback, try asymmetric expansion (in case initial signs same due to weird coefficients)
        a = -1.0
        b = 1.0
        fa = p(a); fb = p(b)
        for k in range(1, max_expand + 1):
            a = - (10.0 ** k)
            b = 10.0 ** k
            fa = p(a); fb = p(b)
            if fa == 0.0:
                return a
            if fb == 0.0:
                return b
            if fa * fb < 0.0:
                break
        else:
            # If still not found, return 0.0 as last resort (shouldn't happen per problem statement)
            return 0.0

    # bisection
    lo, hi = a, b
    flo, fhi = fa, fb
    # ensure flo < 0 < fhi or vice versa
    if flo * fhi > 0.0:
        # swap if needed, but bisection requires opposite signs; fallback
        pass

    tol = 1e-14
    max_iter = 200
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        fmid = p(mid)
        if fmid == 0.0 or (hi - lo) / 2.0 < tol:
            return mid
        if flo * fmid < 0.0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid
    return (lo + hi) / 2.0