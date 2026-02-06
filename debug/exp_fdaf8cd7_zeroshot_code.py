def is_prime(n):
    """Return true if a given number is prime, and false otherwise."""
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    r = int(n**0.5)
    i = 3
    while i <= r:
        if n % i == 0:
            return False
        i += 2
    return True