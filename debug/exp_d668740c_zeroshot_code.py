def multiply(a, b):
    """Return the product of the unit digits of two integers."""
    return (abs(a) % 10) * (abs(b) % 10)