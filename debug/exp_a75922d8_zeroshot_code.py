def fib4(n: int) -> int:
    # Base cases
    if n == 0:
        return 0
    elif n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0
    
    # Initialize the first four elements of the sequence
    fib4_values = [0, 0, 2, 0]
    
    # Compute the sequence iteratively up to the n-th element
    for i in range(4, n + 1):
        next_value = sum(fib4_values)
        fib4_values.pop(0)  # Remove the oldest value
        fib4_values.append(next_value)  # Add the new value
    
    return fib4_values[-1]