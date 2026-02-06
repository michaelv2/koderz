def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def sum_of_digits(n):
    return sum(int(digit) for digit in str(n))

def largest_prime_sum(lst):
    max_prime = None
    for num in lst:
        if is_prime(num) and (max_prime is None or num > max_prime):
            max_prime = num
    return sum_of_digits(max_prime) if max_prime else 0