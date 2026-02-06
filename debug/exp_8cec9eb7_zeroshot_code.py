def compare_one(a, b):
    def to_float(x):
        if isinstance(x, (int, float)):
            return float(x)
        elif isinstance(x, str):
            # Replace comma with dot for decimal separator
            x = x.replace(',', '.')
            return float(x)
        else:
            return float(x)
    
    # Convert to floats for comparison
    a_float = to_float(a)
    b_float = to_float(b)
    
    # Compare and return appropriate value
    if a_float > b_float:
        return a
    elif b_float > a_float:
        return b
    else:
        return None