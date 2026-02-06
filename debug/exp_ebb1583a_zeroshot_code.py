def greatest_common_divisor(a: int, b: int) -> int:
    """Return the greatest common divisor of two integers a and b using the Euclidean algorithm."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a