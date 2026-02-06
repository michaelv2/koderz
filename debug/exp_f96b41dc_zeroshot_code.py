def simplify(x, n):
    # Parse the fractions
    num_x, denom_x = map(int, x.split('/'))
    num_n, denom_n = map(int, n.split('/'))
    
    # Multiply the fractions
    result_num = num_x * num_n
    result_denom = denom_x * denom_n
    
    # Check if the resulting fraction is a whole number
    return result_num % result_denom == 0