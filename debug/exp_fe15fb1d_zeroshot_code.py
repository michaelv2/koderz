def is_multiply_prime(a):
    if a < 2:
        return False
    n = a
    factors = []
    i = 2
    while i * i <= n:
        while n % i == 0:
            factors.append(i)
            n //= i
            if len(factors) > 3:
                return False
        i += 1
    if n > 1:
        factors.append(n)
    return len(factors) == 3