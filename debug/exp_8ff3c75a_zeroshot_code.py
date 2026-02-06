import math

def find_zero(xs: list):
    def poly(x: float) -> float:
        s = 0.0
        # Horner's method for numerical stability and speed
        # xs are coefficients for x^0, x^1, ..., x^n
        # Evaluate from highest degree down: a_n*x^n + ... + a_0
        r = 0.0
        for coeff in reversed(xs):
            r = r * x + coeff
        return r

    # quick check at 0
    f0 = poly(0.0)
    if f0 == 0.0:
        return 0.0

    # initialize interval
    left, right = -1.0, 1.0
    f_left, f_right = poly(left), poly(right)

    # expand interval exponentially until sign change (odd degree guarantees this)
    max_expand = 200
    i = 0
    while f_left * f_right > 0 and i < max_expand:
        left *= 2.0
        right *= 2.0
        f_left = poly(left)
        f_right = poly(right)
        i += 1

    # If no sign change found (extremely unlikely given problem guarantees), return 0
    if f_left * f_right > 0:
        return 0.0

    # If one endpoint is exactly zero, return it
    if f_left == 0.0:
        return left
    if f_right == 0.0:
        return right

    # Bisection to refine root
    for _ in range(200):
        mid = (left + right) / 2.0
        f_mid = poly(mid)
        if f_mid == 0.0:
            return mid
        if f_left * f_mid <= 0:
            right, f_right = mid, f_mid
        else:
            left, f_left = mid, f_mid
    return (left + right) / 2.0