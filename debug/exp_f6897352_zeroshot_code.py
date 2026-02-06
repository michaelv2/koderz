def simplify(x, n):
    # Parse the fractions
    num1, denom1 = map(int, x.split('/'))
    num2, denom2 = map(int, n.split('/'))
    
    # Multiply numerators and denominators
    result_num = num1 * num2
    result_denom = denom1 * denom2
    
    # Check if the result is a whole number
    return result_num % result_denom == 0