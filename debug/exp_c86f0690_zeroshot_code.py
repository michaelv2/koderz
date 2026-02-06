def intersection(interval1, interval2):
    a, b = interval1
    c, d = interval2
    start = max(a, c)
    end = min(b, d)
    if start > end:
        return "NO"
    length = end - start

    def is_prime(n):
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        limit = int(n ** 0.5)
        i = 3
        while i <= limit:
            if n % i == 0:
                return False
            i += 2
        return True

    return "YES" if is_prime(length) else "NO"