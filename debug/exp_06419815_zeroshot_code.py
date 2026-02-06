def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime."""
    largest = -1
    
    # Check for factor 2
    while n % 2 == 0:
        largest = 2
        n = n // 2
    
    # Check for odd factors from 3 onwards
    divisor = 3
    while divisor * divisor <= n:
        while n % divisor == 0:
            largest = divisor
            n = n // divisor
        divisor += 2
    
    # If n is still greater than 1, then it's a prime factor
    if n > 1:
        largest = n
    
    return largest