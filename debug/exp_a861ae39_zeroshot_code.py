def simplify(x, n):
    # Parse the first fraction
    x_num, x_den = map(int, x.split('/'))
    
    # Parse the second fraction
    n_num, n_den = map(int, n.split('/'))
    
    # Multiply the fractions: (x_num/x_den) * (n_num/n_den) = (x_num*n_num)/(x_den*n_den)
    result_num = x_num * n_num
    result_den = x_den * n_den
    
    # Check if the result is a whole number (numerator divisible by denominator)
    return result_num % result_den == 0