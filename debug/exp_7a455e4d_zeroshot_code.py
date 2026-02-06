def special_factorial(n):
    def factorial(m):
        if m == 0 or m == 1:
            return 1
        else:
            return m * factorial(m - 1)
    
    result = 1
    for i in range(1, n + 1):
        result *= factorial(i)
        
    return result