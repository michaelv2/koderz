def int_to_mini_roman(number):
    # Mapping of values to roman numerals in descending order
    # Include subtractive cases (IV, IX, XL, XC, CD, CM)
    val_to_roman = [
        (1000, 'm'),
        (900, 'cm'),
        (500, 'd'),
        (400, 'cd'),
        (100, 'c'),
        (90, 'xc'),
        (50, 'l'),
        (40, 'xl'),
        (10, 'x'),
        (9, 'ix'),
        (5, 'v'),
        (4, 'iv'),
        (1, 'i')
    ]
    
    result = ''
    for value, roman in val_to_roman:
        count = number // value
        if count:
            result += roman * count
            number -= value * count
    
    return result