def hex_key(num):
    primes = set('2357BD')
    return sum(1 for ch in num if ch in primes)