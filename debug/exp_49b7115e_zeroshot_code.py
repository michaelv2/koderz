def multiply(a, b):
    # Extract the unit digit of a and b using the modulo operator
    unit_digit_a = abs(a) % 10
    unit_digit_b = abs(b) % 10

    # Multiply the unit digits together and return the result
    return unit_digit_a * unit_digit_b