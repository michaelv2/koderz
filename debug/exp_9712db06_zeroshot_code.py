def rounded_avg(n, m):
    # Check if n is greater than m
    if n > m:
        return -1
    
    # Calculate the average of numbers from n to m
    avg = sum(range(n, m + 1)) / (m - n + 1)
    
    # Round the average to nearest integer and convert it to binary
    bin_avg = bin(round(avg))
    
    return bin_avg