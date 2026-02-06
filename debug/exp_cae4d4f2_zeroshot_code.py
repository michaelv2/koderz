def truncate_number(number: float) -> float:
    """ Given a positive floating point number, return its decimal part. """
    frac = number - int(number)
    # Avoid returning tiny negative values due to floating point imprecision
    if abs(frac) < 1e-12:
        return 0.0
    return frac