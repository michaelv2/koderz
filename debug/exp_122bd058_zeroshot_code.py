def prime_length(string):
    """Return True if length of string is a prime number, else False."""
    n = len(string)
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True