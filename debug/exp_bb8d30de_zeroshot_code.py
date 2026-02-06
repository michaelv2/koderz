def solve(N):
    # Convert N to binary and remove '0b'
    binary_n = bin(N)[2:]

    # Calculate sum of digits
    sum_digits = sum(int(digit) for digit in binary_n)

    # Convert sum to binary and return
    return bin(sum_digits)[2:]