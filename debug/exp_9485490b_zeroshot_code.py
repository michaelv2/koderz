from math import isqrt

def largest_divisor(n: int) -> int:
    """ For a given number n, find the largest number that divides n evenly, smaller than n """
    if n <= 1:
        return 0
    m = abs(n)
    for i in range(2, isqrt(m) + 1):
        if m % i == 0:
            return m // i
    return 1