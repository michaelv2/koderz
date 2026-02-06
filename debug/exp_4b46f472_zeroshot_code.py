def generate_integers(a, b):
    # Ensure a <= b
    if a > b:
        a, b = b, a
    
    # Even digits are 0, 2, 4, 6, 8
    # Return those that fall within the range [a, b]
    return [digit for digit in range(0, 10) if digit % 2 == 0 and a <= digit <= b]