def modp(n: int, p: int):
    """Return 2^n modulo p."""
    result = 1
    base = 2
    
    while n > 0:
        if n % 2 == 1:
            result = (result * base) % p
        base = (base * base) % p
        n //= 2
    
    return result