def digits(n):
    product = 1
    has_odd = False
    
    for char in str(n):
        digit = int(char)
        if digit % 2 != 0:
            product *= digit
            has_odd = True
    
    return product if has_odd else 0