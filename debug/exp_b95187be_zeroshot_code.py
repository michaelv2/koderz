def f(n):
    if n <= 0:
        return []
    result = []
    fact = 1
    for i in range(1, n + 1):
        fact *= i
        if i % 2 == 0:
            result.append(fact)
        else:
            result.append(i * (i + 1) // 2)
    return result