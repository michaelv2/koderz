def multiply(a, b):
    # Get the unit digit of each number by taking modulo 10
    return (abs(a) % 10) * (abs(b) % 10)