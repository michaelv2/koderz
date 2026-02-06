def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime."""
    # Initialize the smallest prime factor
    factor = 2
    
    # Divide n by 2 until it becomes odd
    while n % factor == 0:
        n //= factor
    
    # Check for odd factors from 3 onwards
    factor = 3
    max_factor = int(n**0.5) + 1
    while factor <= max_factor:
        if n % factor == 0:
            n //= factor
            max_factor = int(n**0.5) + 1
        else:
            factor += 2
    
    # If n is still greater than 2, then it is a prime number and the largest factor
    return n if n > 2 else factor