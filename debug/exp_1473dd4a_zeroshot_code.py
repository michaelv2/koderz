def special_factorial(n):
    # Initialize result as 1
    result = 1

    # Multiply result by n factorial for each number from 1 to n
    for i in range(1, n + 1):
        fact = 1
        for j in range(1, i + 1):
            fact *= j
        result *= fact
    
    return result