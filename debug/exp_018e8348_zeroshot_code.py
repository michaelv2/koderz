def int_to_mini_roman(number):
    # Define the mapping of values to Roman numerals in descending order
    values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    numerals = ['m', 'cm', 'd', 'cd', 'c', 'xc', 'l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
    
    result = ""
    
    # Process each value from largest to smallest
    for i in range(len(values)):
        # Add the numeral as many times as the value fits into the number
        count = number // values[i]
        if count > 0:
            result += numerals[i] * count
            number -= values[i] * count
    
    return result