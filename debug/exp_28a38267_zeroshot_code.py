def is_prime(num):
    """Helper function to check if a number is prime."""
    if num <= 1:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def count_up_to(n):
    """Function that returns the first n prime numbers less than n."""
    primes = []
    num = 2
    while len(primes) < n and num < n:
        if is_prime(num):
            primes.append(num)
        num += 1
    return primes