def compare_one(a, b):
    def to_num(x):
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip().replace(',', '.')
            return float(s)
        raise TypeError("Unsupported type for comparison")
    
    va = to_num(a)
    vb = to_num(b)
    if va == vb:
        return None
    return a if va > vb else b