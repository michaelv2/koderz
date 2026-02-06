def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime."""
    # Remove all factors of 2
    while n % 2 == 0:
        n //= 2
    
    # Check for odd factors from 3 to sqrt(n)
    factor = 3
    while factor * factor <= n:
        while n % factor == 0:
            n //= factor
        factor += 2
    
    # If n is still greater than 2, then it is prime
    return n if n > 2 else factor - 2