def is_prime(n):
    """Check if n is prime."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def sum_of_digits(n):
    """Return the sum of digits of n."""
    return sum(int(i) for i in str(n))

def largest_prime_sum(lst):
    """Find the largest prime and return the sum of its digits."""
    primes = [x for x in lst if is_prime(x)]
    if not primes:
        return 0
    else:
        return sum_of_digits(max(primes))