def count_up_to(n):
    if n <= 2:
        return []
    sieve = [True] * n
    sieve[0] = sieve[1] = False
    p = 2
    while p * p < n:
        if sieve[p]:
            for i in range(p * p, n, p):
                sieve[i] = False
        p += 1
    return [i for i, is_prime in enumerate(sieve) if is_prime]