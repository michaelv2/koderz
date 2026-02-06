def skjkasdkd(lst):
    """Return the sum of digits of the largest prime value found in lst.
    If no prime is present, return 0.
    """
    def is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        limit = int(n ** 0.5)
        d = 3
        while d <= limit:
            if n % d == 0:
                return False
            d += 2
        return True

    max_prime = None
    for x in lst:
        if isinstance(x, int) and is_prime(x):
            if max_prime is None or x > max_prime:
                max_prime = x

    if max_prime is None:
        return 0

    return sum(int(ch) for ch in str(max_prime))