def is_multiply_prime(a):
    def is_prime(n):
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    # Find prime factors and count them
    prime_factors = []
    temp = a
    
    # Check for factor 2
    while temp % 2 == 0:
        prime_factors.append(2)
        temp //= 2
    
    # Check for odd factors from 3 onwards
    i = 3
    while i * i <= temp:
        while temp % i == 0:
            prime_factors.append(i)
            temp //= i
        i += 2
    
    # If temp is still greater than 1, then it's a prime factor
    if temp > 1:
        prime_factors.append(temp)
    
    # Check if we have exactly 3 prime factors
    return len(prime_factors) == 3