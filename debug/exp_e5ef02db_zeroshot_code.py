def change_base(x: int, base: int) -> str:
    if x == 0:
        return "0"
    
    digits = []
    while x > 0:
        remainder = x % base
        digits.append(str(remainder))
        x = x // base
    
    # Reverse the list of digits and join them into a string
    return ''.join(digits[::-1])