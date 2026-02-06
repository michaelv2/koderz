def even_odd_count(num):
    # Convert the number to positive if it's negative
    num = abs(num)
    
    # Initialize counters for even and odd digits
    even_count = 0
    odd_count = 0
    
    # Iterate over each digit in the number
    while num > 0:
        digit = num % 10
        
        # If the digit is even, increment the even counter
        if digit % 2 == 0:
            even_count += 1
        else:
            odd_count += 1
            
        # Remove the last digit from the number
        num //= 10
    
    return (even_count, odd_count)