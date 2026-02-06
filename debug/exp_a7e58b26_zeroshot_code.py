def skjkasdkd(lst):
    def is_prime(n):
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def sum_of_digits(n):
        return sum(int(digit) for digit in str(n))
    
    # Find all prime numbers in the list
    primes = [num for num in lst if is_prime(num)]
    
    # If no primes found, return 0 (though based on examples, there should be primes)
    if not primes:
        return 0
    
    # Find the largest prime
    largest_prime = max(primes)
    
    # Return the sum of its digits
    return sum_of_digits(largest_prime)