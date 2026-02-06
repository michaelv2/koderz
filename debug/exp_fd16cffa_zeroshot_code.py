def is_multiply_prime(a):
    """Returns true if the given number is the multiplication of 3 prime numbers."""
    prime_count = 0
    
    # Check for factor 2
    while a % 2 == 0:
        prime_count += 1
        a //= 2
    
    # Check for odd factors from 3 onwards
    divisor = 3
    while divisor * divisor <= a:
        while a % divisor == 0:
            prime_count += 1
            a //= divisor
        divisor += 2
    
    # If a is still greater than 1, then it's a prime factor
    if a > 1:
        prime_count += 1
    
    return prime_count == 3