def prime_fib(n: int):
    """
    prime_fib returns n-th number that is a Fibonacci number and it's also prime.
    >>> prime_fib(1)
    2
    >>> prime_fib(2)
    3
    >>> prime_fib(3)
    5
    >>> prime_fib(4)
    13
    >>> prime_fib(5)
    89
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    def is_prime(num: int) -> bool:
        if num < 2:
            return False
        small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
        for p in small_primes:
            if num == p:
                return True
            if num % p == 0:
                return False
        # write num-1 as d * 2^s
        d = num - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        # bases good for testing up to 2^64 deterministically
        bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
        for a in bases:
            if a % num == 0:
                continue
            x = pow(a, d, num)
            if x == 1 or x == num - 1:
                continue
            composite = True
            for _ in range(s - 1):
                x = (x * x) % num
                if x == num - 1:
                    composite = False
                    break
            if composite:
                return False
        return True

    count = 0
    a, b = 1, 1  # Fibonacci sequence: 1,1,2,3,5,...
    while True:
        if a >= 2 and is_prime(a):
            count += 1
            if count == n:
                return a
        a, b = b, a + b