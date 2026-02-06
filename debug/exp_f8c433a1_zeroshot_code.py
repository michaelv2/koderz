def compare_one(a, b):
    # Helper function to convert any input to a float for comparison
    def to_float(val):
        if isinstance(val, str):
            return float(val.replace(",", "."))
        return float(val)
    
    # Convert both to float for comparison
    a_float = to_float(a)
    b_float = to_float(b)
    
    # Compare and return
    if a_float > b_float:
        return a
    elif b_float > a_float:
        return b
    else:
        return None