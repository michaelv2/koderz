def derivative(xs: list):
    return [i * x for i, x in enumerate(xs) if i > 0]