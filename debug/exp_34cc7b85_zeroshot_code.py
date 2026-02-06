def skjkasdkd(lst):
    def is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        if n % 3 == 0:
            return n == 3
        i = 5
        while i * i <= n:
            if n % i == 0:
                return False
            if n % (i + 2) == 0:
                return False
            i += 6
        return True

    max_prime = None
    for v in lst:
        if isinstance(v, int) and is_prime(v):
            if max_prime is None or v > max_prime:
                max_prime = v

    if max_prime is None:
        return 0
    return sum(int(d) for d in str(max_prime))