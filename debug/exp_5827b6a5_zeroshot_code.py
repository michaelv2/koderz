def compare_one(a, b):
    def to_num(x):
        if isinstance(x, str):
            s = x.strip().replace(',', '.')
            return float(s)
        if isinstance(x, (int, float)):
            return float(x)
        raise TypeError("Unsupported type")
    na = to_num(a)
    nb = to_num(b)
    if na == nb:
        return None
    return a if na > nb else b