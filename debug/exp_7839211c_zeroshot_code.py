def largest_prime_factor(n: int) -> int:
    """Return the largest prime factor of n. Assume n > 1 and is not a prime.
    >>> largest_prime_factor(13195)
    29
    >>> largest_prime_factor(2048)
    2
    """
    last_factor = 1

    # Remove factors of 2
    while n % 2 == 0:
        last_factor = 2
        n //= 2

    # Check odd factors starting from 3
    f = 3
    while f * f <= n:
        while n % f == 0:
            last_factor = f
            n //= f
        f += 2

    # If remaining n > 1, it's a prime factor
    if n > 1:
        last_factor = n

    return last_factor