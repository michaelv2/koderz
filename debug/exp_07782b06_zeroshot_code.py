def count_up_to(n):
    if n <= 2:
        return []
    sieve = [True] * n
    sieve[0] = sieve[1] = False
    i = 2
    while i * i < n:
        if sieve[i]:
            j = i * i
            while j < n:
                sieve[j] = False
                j += i
        i += 1
    return [i for i, is_prime in enumerate(sieve) if is_prime]