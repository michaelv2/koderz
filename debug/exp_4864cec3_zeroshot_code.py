def hex_key(num):
    # Define the set of prime hexadecimal digits
    prime_hex_digits = {'2', '3', '5', '7', 'B', 'D'}
    
    # Initialize a counter for prime digits
    prime_count = 0
    
    # Iterate over each character in the input string
    for char in num:
        # Check if the character is a prime digit
        if char in prime_hex_digits:
            # Increment the counter if it is a prime digit
            prime_count += 1
    
    # Return the total count of prime digits
    return prime_count