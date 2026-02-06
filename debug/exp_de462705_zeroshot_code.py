def fib4(n):
    # Initialize the first four numbers of the sequence
    fib_sequence = [0, 0, 2, 0]
    
    if n <= 3:
        return fib_sequence[n]
    else:
        for i in range(4, n+1):
            # Compute each number as the sum of the previous four numbers
            next_number = sum(fib_sequence)
            
            # Update the sequence with the new number
            fib_sequence.append(next_number)
            
            # Remove the first element to keep only the last four elements
            fib_sequence.pop(0)
        
        return fib_sequence[-1]