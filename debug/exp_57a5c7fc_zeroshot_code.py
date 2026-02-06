def largest_divisor(n: int) -> int:
    """ For a given number n, find the largest number that divides n evenly, smaller than n """
    if n <= 1:
        return 0
    for i in range(n // 2, 0, -1):
        if n % i == 0:
            return i