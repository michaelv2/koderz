def f(n):
    def factorial(num):
        result = 1
        for i in range(2, num + 1):
            result *= i
        return result
    
    result = []
    for i in range(1, n+1):
        if i % 2 == 0:
            result.append(factorial(i))
        else:
            result.append(sum(range(i + 1)))
            
    return result