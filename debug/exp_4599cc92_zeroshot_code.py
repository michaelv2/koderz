def simplify(x, n):
    # Parse the first fraction
    x_parts = x.split('/')
    x_num = int(x_parts[0])
    x_den = int(x_parts[1])
    
    # Parse the second fraction
    n_parts = n.split('/')
    n_num = int(n_parts[0])
    n_den = int(n_parts[1])
    
    # Multiply the fractions: (x_num/x_den) * (n_num/n_den)
    result_num = x_num * n_num
    result_den = x_den * n_den
    
    # Check if the result is a whole number
    return result_num % result_den == 0