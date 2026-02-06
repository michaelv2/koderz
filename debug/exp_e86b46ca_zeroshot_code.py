def solve(N):
    # Calculate sum of digits
    digit_sum = sum(int(digit) for digit in str(N))
    
    # Convert sum to binary and remove '0b' prefix
    binary_result = bin(digit_sum)[2:]
    
    return binary_result