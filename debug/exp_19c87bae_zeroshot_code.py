def fibfib(n: int):
    if n == 0:
        return 0
    elif n == 1:
        return 0
    elif n == 2:
        return 1
    
    # Initialize the first three values
    a, b, c = 0, 0, 1
    
    # Compute iteratively from 3 to n
    for i in range(3, n + 1):
        next_val = a + b + c
        a, b, c = b, c, next_val
    
    return c