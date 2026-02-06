def int_to_mini_roman(number):
    """
    Given a positive integer, obtain its roman numeral equivalent as a string,
    and return it in lowercase.
    Restrictions: 1 <= num <= 1000
    """
    if not isinstance(number, int):
        raise TypeError("number must be int")
    if number < 1 or number > 1000:
        raise ValueError("number must be between 1 and 1000 inclusive")

    mapping = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]

    result = []
    n = number
    for val, sym in mapping:
        while n >= val:
            result.append(sym)
            n -= val
        if n == 0:
            break

    return ''.join(result).lower()