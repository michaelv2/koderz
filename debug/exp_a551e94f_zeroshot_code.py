def fib4(n: int) -> int:
    if n < 4:
        return [0, 0, 2, 0][n]
    
    # Initialize the first four values of the sequence
    a, b, c, d = 0, 0, 2, 0
    
    # Compute the n-th value iteratively
    for _ in range(4, n + 1):
        a, b, c, d = b, c, d, a + b + c + d
    
    return d