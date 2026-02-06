def solve(N):
    # Convert N to binary, remove the '0b' prefix, and sum the digits
    binary_sum = sum(int(digit) for digit in bin(N)[2:])
    # Convert the sum to a binary string and return it
    return bin(binary_sum)[2:]