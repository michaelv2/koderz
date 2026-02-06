def skjkasdkd(lst):
    """You are given a list of integers.
    You need to find the largest prime value and return the sum of its digits.
    """
    def is_prime(n):
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

    max_p = None
    for x in lst:
        if isinstance(x, int) and x > 1 and is_prime(x):
            if max_p is None or x > max_p:
                max_p = x
    if max_p is None:
        return 0
    return sum(int(ch) for ch in str(abs(max_p)))