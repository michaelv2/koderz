def prime_fib(n: int):
    """
    prime_fib returns n-th number that is a Fibonacci number and it's also prime.
    """
    import math

    def is_prime(x: int) -> bool:
        if x <= 1:
            return False
        if x <= 3:
            return True
        if x % 2 == 0:
            return False
        r = math.isqrt(x)
        i = 3
        while i <= r:
            if x % i == 0:
                return False
            i += 2
        return True

    if n <= 0:
        raise ValueError("n must be a positive integer")
    count = 0
    a, b = 0, 1
    while True:
        a, b = b, a + b
        if is_prime(a):
            count += 1
            if count == n:
                return a