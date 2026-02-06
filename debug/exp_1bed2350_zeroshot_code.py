def compare_one(a, b):
    # Convert string numbers to float
    if type(a) == str and ',' in a:
        a = float(a.replace(',', '.'))
    if type(b) == str and ',' in b:
        b = float(b.replace(',', '.'))
    
    # Compare the variables
    if a > b:
        return a
    elif b > a:
        return b
    else:
        return None