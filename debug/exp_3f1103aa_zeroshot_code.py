import math

def truncate_number(number: float) -> float:
    """Return the decimal part of a non-negative floating point number."""
    return number - math.floor(number)