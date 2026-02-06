def get_odd_collatz(n):
    odd_numbers = set()
    current = n
    
    while current != 1:
        if current % 2 == 1:  # if current number is odd
            odd_numbers.add(current)
        
        if current % 2 == 0:  # if current number is even
            current = current // 2
        else:  # if current number is odd
            current = 3 * current + 1
    
    # Add 1 to the set since the sequence always ends at 1
    odd_numbers.add(1)
    
    # Return sorted list
    return sorted(list(odd_numbers))