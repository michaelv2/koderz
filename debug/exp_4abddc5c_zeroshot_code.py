def solve(N):
    # Calculate sum of digits
    digit_sum = sum(int(digit) for digit in str(N))
    
    # Convert to binary and remove the '0b' prefix
    return bin(digit_sum)[2:]