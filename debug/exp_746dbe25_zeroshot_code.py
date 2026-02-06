def is_multiply_prime(a):
    if not isinstance(a, int) or a < 0:
        return False
    if a < 8:
        return False  # smallest product of three primes is 2*2*2 = 8
    n = a
    count = 0
    p = 2
    while p * p <= n:
        while n % p == 0:
            n //= p
            count += 1
            if count > 3:
                return False
        p += 1
    if n > 1:
        count += 1
    return count == 3