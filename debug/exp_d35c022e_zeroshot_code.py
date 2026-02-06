def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime."""
    # Start with the smallest prime number
    factor = 2
    
    # Divide n by 2 until it is no longer divisible by 2
    while n % factor == 0:
        n //= factor
    
    # Check for odd factors from 3 onwards
    factor = 3
    while factor * factor <= n:
        while n % factor == 0:
            n //= factor
        factor += 2
    
    # If n is still greater than 1, then it is the largest prime factor
    return n if n > 1 else factor - 2