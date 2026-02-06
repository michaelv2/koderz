def special_factorial(n):
    def factorial(x):
        if x == 0 or x == 1:
            return 1
        result = 1
        for i in range(2, x + 1):
            result *= i
        return result
    
    brazilian_factorial = 1
    for i in range(n, 0, -1):
        brazilian_factorial *= factorial(i)
    
    return brazilian_factorial