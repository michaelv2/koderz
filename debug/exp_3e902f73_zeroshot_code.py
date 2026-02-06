def convert_to_float(x):
    if isinstance(x, str):
        x = x.replace(",", ".")
        return float(x)
    else:
        return float(x)

def compare_one(a, b):
    a_float = convert_to_float(a)
    b_float = convert_to_float(b)

    if a_float == b_float:
        return None
    elif a_float > b_float:
        return type(a)(a)
    else:
        return type(b)(b)