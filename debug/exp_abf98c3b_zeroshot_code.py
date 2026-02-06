def count_up_to(n):
    if n <= 2:
        return []
    m = int(n)
    sieve = [True] * m
    sieve[0] = False
    if m > 1:
        sieve[1] = False
    limit = int(m ** 0.5)
    for p in range(2, limit + 1):
        if sieve[p]:
            for j in range(p * p, m, p):
                sieve[j] = False
    return [i for i in range(2, m) if sieve[i]]