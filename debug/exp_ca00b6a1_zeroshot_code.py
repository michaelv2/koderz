def compare_one(a, b):
    """
    Take two values which may be int, float, or numeric strings
    (commas or dots as decimal separators). Compare their numeric values
    and return the one that is larger in its original type. If equal, return None.
    """
    def to_num(x):
        if isinstance(x, (int, float, bool)):
            return float(x)
        if isinstance(x, str):
            s = x.strip().replace(',', '.')
            return float(s)
        raise TypeError("Unsupported type")

    va = to_num(a)
    vb = to_num(b)

    if va == vb:
        return None
    return a if va > vb else b