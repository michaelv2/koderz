def intersection(interval1, interval2):
    def is_prime(n):
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        i = 3
        while i * i <= n:
            if n % i == 0:
                return False
            i += 2
        return True

    a, b = interval1
    c, d = interval2
    start = max(a, c)
    end = min(b, d)
    if start > end:
        return "NO"
    length = end - start
    return "YES" if is_prime(length) else "NO"