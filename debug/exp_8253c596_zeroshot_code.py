def int_to_mini_roman(number):
    values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    
    n = int(number)
    parts = []
    
    for v, s in zip(values, symbols):
        if n == 0:
            break
        count = n // v
        if count:
            parts.append(s * count)
            n -= v * count
    
    return "".join(parts).lower()