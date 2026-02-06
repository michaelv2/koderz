def is_multiply_prime(a):
    if not isinstance(a, int) or a < 2:
        return False
    n = a
    count = 0
    p = 2
    while p * p <= n:
        while n % p == 0:
            count += 1
            n //= p
            if count > 3:
                return False
        p += 1
    if n > 1:
        count += 1
    return count == 3