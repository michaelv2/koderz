def hex_key(num):
    # Define a set of prime hexadecimal digits for quick lookup
    prime_hex_digits = {'2', '3', '5', '7', 'B', 'D'}
    
    # Initialize a counter for prime digits
    count = 0
    
    # Iterate through each character in the input string
    for char in num:
        # Check if the character is a prime hexadecimal digit
        if char in prime_hex_digits:
            count += 1
    
    return count