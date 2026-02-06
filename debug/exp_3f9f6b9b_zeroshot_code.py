from typing import List

def factorize(n: int) -> List[int]:
    """ Return list of prime factors of given integer in the order from smallest to largest.
    Each of the factors should be listed number of times corresponding to how many times it appeares in factorization.
    Input number should be equal to the product of all factors
    """
    factors: List[int] = []
    if n == 0:
        raise ValueError("Cannot factorize zero")
    if n < 0:
        factors.append(-1)
        n = -n
    if n == 1:
        return factors
    # factor out 2s
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    # factor odd numbers
    p = 3
    while p * p <= n:
        while n % p == 0:
            factors.append(p)
            n //= p
        p += 2
    if n > 1:
        factors.append(n)
    return factors