def is_prime(n):
    """Return true if a given number is prime, and false otherwise."""
    if not isinstance(n, int) or n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False
    i = 3
    limit = int(n**0.5) + 1
    while i <= limit:
        if n % i == 0:
            return False
        i += 2
    return True