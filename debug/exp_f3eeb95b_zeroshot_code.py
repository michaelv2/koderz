def multiply(a, b):
    # Get the unit digits of both numbers by taking modulo 10
    unit_digit_a = abs(a) % 10
    unit_digit_b = abs(b) % 10
    
    # Return the product of these two units
    return unit_digit_a * unit_digit_b