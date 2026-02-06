def tri(n):
    def fibonacci(n):
        if n == 0 or n == 1:
            return n
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    
    sequence = []
    for i in range(n+1):
        if i % 2 == 0:
            sequence.append(int(1 + (i / 2)))
        else:
            sequence.append(fibonacci(i-1) + fibonacci(i-2) + fibonacci(i+1))
    return sequence