def skjkasdkd(lst):
    def is_prime(n: int) -> bool:
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    max_prime = None
    for x in lst:
        if is_prime(x):
            if max_prime is None or x > max_prime:
                max_prime = x

    if max_prime is None:
        return 0
    return sum(int(d) for d in str(max_prime))