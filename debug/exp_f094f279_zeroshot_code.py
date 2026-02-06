def fib(n):
    # Initialize the first two Fibonacci numbers
    a, b = 0, 1
    
    # Calculate the n-th Fibonacci number iteratively
    for _ in range(n):
        a, b = b, a + b
        
    return a