def fibfib(n: int) -> int:
    if n == 0 or n == 1:
        return 0
    elif n == 2:
        return 1
    
    # Initialize an array to store computed values
    fibfib_values = [0] * (n + 1)
    fibfib_values[0] = 0
    fibfib_values[1] = 0
    fibfib_values[2] = 1
    
    # Compute the sequence iteratively
    for i in range(3, n + 1):
        fibfib_values[i] = fibfib_values[i - 1] + fibfib_values[i - 2] + fibfib_values[i - 3]
    
    return fibfib_values[n]