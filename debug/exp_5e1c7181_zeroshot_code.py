def is_multiply_prime(a):
    """Write a function that returns true if the given number is the multiplication of 3 prime numbers
    and false otherwise.
    Knowing that (a) is less then 100. 
    Example:
    is_multiply_prime(30) == True
    30 = 2 * 3 * 5
    """
    if a < 8:
        return False
    def is_prime(n):
        if n < 2:
            return False
        i = 2
        while i * i <= n:
            if n % i == 0:
                return False
            i += 1
        return True
    primes = [p for p in range(2, a + 1) if is_prime(p)]
    for i in range(len(primes)):
        p = primes[i]
        if p * 2 * 2 > a:
            # smallest possible product with p exceeds a
            continue
        for j in range(len(primes)):
            q = primes[j]
            if p * q * 2 > a:
                continue
            for k in range(len(primes)):
                r = primes[k]
                if p * q * r == a:
                    return True
    return False