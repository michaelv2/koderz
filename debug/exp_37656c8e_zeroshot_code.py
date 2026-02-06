def hex_key(num):
    """Count hex digits that are prime numbers: 2,3,5,7,B(11),D(13)."""
    primes = {'2', '3', '5', '7', 'B', 'D'}
    return sum(1 for ch in num if ch in primes)