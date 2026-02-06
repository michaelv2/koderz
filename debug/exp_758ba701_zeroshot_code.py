import math

def truncate_number(number: float) -> float:
    """Return the decimal part (fractional component) of a non-negative float.

    The fractional part is number - floor(number).
    """
    if number < 0:
        raise ValueError("number must be non-negative")
    return number - math.floor(number)