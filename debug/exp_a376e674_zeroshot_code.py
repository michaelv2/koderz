def generate_integers(a, b):
    lo, hi = (a, b) if a <= b else (b, a)
    return [d for d in (2, 4, 6, 8) if lo <= d <= hi]