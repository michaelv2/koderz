def compare_one(a, b):
    # Helper function to convert string to float if necessary
    def to_float(value):
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    
    # Convert both inputs to floats for comparison
    a_float = to_float(a)
    b_float = to_float(b)
    
    # Compare the values
    if a_float == b_float:
        return None
    elif a_float > b_float:
        return a
    else:
        return b