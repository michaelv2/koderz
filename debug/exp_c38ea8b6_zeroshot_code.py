def skjkasdkd(lst):
    def is_prime(n):
        if n < 2:
            return False
        small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
        for p in small_primes:
            if n == p:
                return True
            if n % p == 0:
                return False
        # Miller-Rabin deterministic bases for 64-bit integers
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
        for a in bases:
            if a % n == 0:
                continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            composite = True
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1:
                    composite = False
                    break
            if composite:
                return False
        return True

    max_prime = None
    for v in lst:
        if v is None:
            continue
        if v >= 2 and is_prime(v):
            if max_prime is None or v > max_prime:
                max_prime = v
    if max_prime is None:
        return 0
    return sum(int(ch) for ch in str(abs(max_prime)))