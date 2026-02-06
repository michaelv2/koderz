def skjkasdkd(lst):
    def is_prime(n):
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    max_p = -1
    for x in lst:
        if isinstance(x, int) and is_prime(x) and x > max_p:
            max_p = x

    if max_p == -1:
        return 0

    s = 0
    n = max_p
    while n:
        s += n % 10
        n //= 10
    return s