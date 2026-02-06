def x_or_y(n, x, y):
    """
    Return x if n is prime, otherwise return y.
    Primes are integers greater than 1 with no positive divisors other than 1 and itself.
    """
    def is_prime(num):
        if num <= 1:
            return False
        if num <= 3:
            return True
        if num % 2 == 0 or num % 3 == 0:
            return False
        i = 5
        while i * i <= num:
            if num % i == 0 or num % (i + 2) == 0:
                return False
            i += 6
        return True

    return x if is_prime(n) else y