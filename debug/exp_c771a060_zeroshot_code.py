def string_sequence(n: int) -> str:
    """Return a string containing space-delimited numbers starting from 0 up to n inclusive."""
    return " ".join(map(str, range(n + 1)))