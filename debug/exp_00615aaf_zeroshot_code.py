def rounded_avg(n, m):
    if n > m:
        return -1
    
    # Calculate sum of integers from n to m
    total = sum(range(n, m + 1))
    count = m - n + 1
    
    # Calculate average and round to nearest integer
    average = total / count
    rounded = round(average)
    
    # Convert to binary
    return bin(rounded)