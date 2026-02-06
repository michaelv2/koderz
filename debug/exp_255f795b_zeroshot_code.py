def hex_key(num):
    # Set of hexadecimal digits that represent prime numbers
    prime_hex_digits = {'2', '3', '5', '7', 'B', 'D'}
    
    # Count how many digits in the input are prime hex digits
    count = 0
    for digit in num:
        if digit in prime_hex_digits:
            count += 1
    
    return count