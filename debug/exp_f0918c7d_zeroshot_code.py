def compare_one(a, b):
    """
    Return the larger variable in its original type, comparing numeric values.
    If the numeric values are equal, return None.
    Strings may represent real numbers and may use '.' or ',' as decimal separator.
    """
    def to_number(x):
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip()
            if not s:
                raise ValueError("Empty string cannot be parsed as a number")
            try:
                return float(s)
            except ValueError:
                # Handle decimal comma representation, e.g., "2,3"
                s2 = s.replace(',', '.')
                return float(s2)
        raise TypeError("Unsupported type for numeric comparison")

    na = to_number(a)
    nb = to_number(b)

    if na == nb:
        return None
    return a if na > nb else b