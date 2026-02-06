def prime_fib(n: int):
    def is_prime(num):
        if num < 2:
            return False
        if num == 2:
            return True
        if num % 2 == 0:
            return False
        for i in range(3, int(num**0.5) + 1, 2):
            if num % i == 0:
                return False
        return True
    
    count = 0
    a, b = 1, 1
    
    while count < n:
        a, b = b, a + b
        if is_prime(b):
            count += 1
    
    return b