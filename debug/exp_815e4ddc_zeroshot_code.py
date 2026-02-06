def count_up_to(n):
    """Return a list of all prime numbers strictly less than n."""
    if n <= 2:
        return []
    sieve = [True] * n
    sieve[0] = sieve[1] = False
    limit = int(n ** 0.5)
    for p in range(2, limit + 1):
        if sieve[p]:
            for multiple in range(p * p, n, p):
                sieve[multiple] = False
    return [i for i in range(2, n) if sieve[i]]