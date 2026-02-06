def change_base(x: int, base: int):
    # Create an empty string to store the result
    result = ''
    
    # Loop until x is greater than 0
    while x > 0:
        # Get the remainder of x divided by base
        remainder = x % base
        
        # Add the remainder to the beginning of the result string
        result = str(remainder) + result
        
        # Update x to be the integer division of x by base
        x //= base
    
    return result