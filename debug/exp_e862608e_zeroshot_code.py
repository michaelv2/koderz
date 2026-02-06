def is_multiply_prime(a):
    primes = [2, 3, 5, 7]
    
    # Check all possible combinations of three prime numbers
    for i in range(len(primes)):
        for j in range(i+1, len(primes)):
            for k in range(j+1, len(primes)):
                if primes[i] * primes[j] * primes[k] == a:
                    return True
    return False