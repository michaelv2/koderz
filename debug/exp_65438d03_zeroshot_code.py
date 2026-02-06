def solve(N):
    # Calculate the sum of the digits of N
    digit_sum = sum(int(digit) for digit in str(N))
    
    # Convert the sum to a binary string and return it
    return bin(digit_sum)[2:]