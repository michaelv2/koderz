def truncate_number(number: float) -> float:
    """Return the decimal part of a positive floating point number."""
    import math
    return number - math.floor(number)