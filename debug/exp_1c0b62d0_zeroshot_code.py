def derivative(xs: list):
    return [(i + 1) * xs[i + 1] for i in range(len(xs) - 1)]