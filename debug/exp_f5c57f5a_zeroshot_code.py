import math

def truncate_number(number: float) -> float:
    """Return the fractional (decimal) part of a positive floating point number."""
    return number - math.floor(number)