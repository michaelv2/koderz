def multiply(a, b):
    """Return the product of the unit digits (last digits of absolute values) of a and b."""
    return (abs(a) % 10) * (abs(b) % 10)