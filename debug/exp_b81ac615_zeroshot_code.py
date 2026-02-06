def is_multiply_prime(a):
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
    ln = len(primes)
    for i in range(ln):
        for j in range(i, ln):
            for k in range(j, ln):
                if primes[i] * primes[j] * primes[k] == a:
                    return True
    return False