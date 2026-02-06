def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime.
    >>> largest_prime_factor(13195)
    29
    >>> largest_prime_factor(2048)
    2
    """
    # remove factors of 2
    largest = None
    while n % 2 == 0:
        largest = 2
        n //= 2
    # check odd factors
    i = 3
    while i * i <= n:
        while n % i == 0:
            largest = i
            n //= i
        i += 2
    # if remaining n > 1, it is a prime factor
    if n > 1:
        largest = n
    return int(largest)