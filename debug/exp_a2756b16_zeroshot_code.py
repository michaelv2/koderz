def f(n):
    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:
            # Calculate factorial of i
            factorial = 1
            for j in range(1, i + 1):
                factorial *= j
            result.append(factorial)
        else:
            # Calculate sum from 1 to i
            summation = sum(range(1, i + 1))
            result.append(summation)
    return result