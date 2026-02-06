def is_prime(num):
    """Check if a number is prime."""
    if num <= 1:
        return False
    if num <= 3:
        return True
    if num % 2 == 0 or num % 3 == 0:
        return False
    i = 5
    while i * i <= num:
        if num % i == 0 or num % (i + 2) == 0:
            return False
        i += 6
    return True

def fibonacci():
    """Generate Fibonacci numbers indefinitely."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def prime_fib(n: int):
    """Return the n-th number that is both a Fibonacci number and prime."""
    fib_gen = fibonacci()
    count = 0
    while True:
        fib_num = next(fib_gen)
        if is_prime(fib_num):
            count += 1
            if count == n:
                return fib_num