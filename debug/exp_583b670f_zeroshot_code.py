def multiply(a, b):
    """Complete the function that takes two integers and returns 
    the product of their unit digits.
    Assume the input is always valid.
    """
    return (abs(a) % 10) * (abs(b) % 10)