def rounded_avg(n, m):
    if n > m:
        return -1
    from fractions import Fraction
    return bin(round(Fraction(n + m, 2)))