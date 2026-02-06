def f(n):
    def factorial(i):
        if i == 0 or i == 1:
            return 1
        else:
            return i * factorial(i - 1)
    
    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:
            result.append(factorial(i))
        else:
            result.append((i * (i + 1)) // 2)
            
    return result