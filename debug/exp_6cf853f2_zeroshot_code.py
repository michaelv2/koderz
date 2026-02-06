def is_multiply_prime(a):
    # List of prime numbers less than 100
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    
    # Check all combinations of three primes
    for i in range(len(primes)):
        for j in range(i, len(primes)):
            for k in range(j, len(primes)):
                if primes[i] * primes[j] * primes[k] == a:
                    return True
    return False