def solve(N):
    # Convert the integer to binary and remove the '0b' prefix
    binary = bin(N)[2:]
    
    # Initialize sum variable
    total = 0
    
    # Iterate over each digit in the binary representation
    for digit in binary:
        # Add the digit (which is a string) to the total as an integer
        total += int(digit)
        
    # Convert the total back to binary and return it, removing the '0b' prefix
    return bin(total)[2:]