def generate_integers(a, b):
    lo, hi = (a, b) if a <= b else (b, a)
    start = max(lo, 1)  # single-digit positive numbers start at 1
    end = min(hi, 9)    # consider only single-digit numbers (0-9)
    return [d for d in range(start, end + 1) if d % 2 == 0]