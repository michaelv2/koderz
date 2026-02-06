def fib4(n: int):
    if n == 0:
        return 0
    elif n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0
    
    # Initialize the first four values
    a, b, c, d = 0, 0, 2, 0  # fib4(0), fib4(1), fib4(2), fib4(3)
    
    # Iteratively compute fib4(n)
    for i in range(4, n + 1):
        next_val = a + b + c + d
        # Slide the window
        a, b, c, d = b, c, d, next_val
    
    return d