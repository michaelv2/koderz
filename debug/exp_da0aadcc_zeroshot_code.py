def fib4(n: int) -> int:
    if n == 0 or n == 1 or n == 3:
        return 0
    if n == 2:
        return 2
    
    # Initialize the first four values of the sequence
    fib4_values = [0, 0, 2, 0]
    
    # Compute the sequence iteratively up to n
    for i in range(4, n + 1):
        next_value = sum(fib4_values)
        # Update the list to hold the last four values
        fib4_values = [fib4_values[1], fib4_values[2], fib4_values[3], next_value]
    
    return fib4_values[-1]