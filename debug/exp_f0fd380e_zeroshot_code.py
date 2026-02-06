def string_sequence(n: int) -> str:
    """Return a space-delimited string of numbers from 0 to n inclusive."""
    return ' '.join(str(i) for i in range(n + 1))