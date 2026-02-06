def hex_key(num):
    if not num:
        return 0
    primes = {'2', '3', '5', '7', 'B', 'D'}
    count = 0
    for ch in num:
        if ch.upper() in primes:
            count += 1
    return count