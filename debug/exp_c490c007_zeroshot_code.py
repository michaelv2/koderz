def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assumes n > 1 and n is not prime."""
    if n <= 1:
        raise ValueError("n must be greater than 1")
    last_factor = 1

    # Factor out powers of 2
    while n % 2 == 0:
        last_factor = 2
        n //= 2

    # Factor out odd primes
    p = 3
    while p * p <= n:
        while n % p == 0:
            last_factor = p
            n //= p
        p += 2

    # If remaining n is > 1, it's a prime factor larger than sqrt(original n)
    if n > 1:
        last_factor = n

    return last_factor