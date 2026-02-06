def simplify(x, n):
    # Split the fractions into numerator and denominator
    x_num, x_denom = map(int, x.split('/'))
    n_num, n_denom = map(int, n.split('/'))
    
    # Multiply the numerators and denominators
    result_num = x_num * n_num
    result_denom = x_denom * n_denom
    
    # Check if the product is a whole number
    return result_num % result_denom == 0