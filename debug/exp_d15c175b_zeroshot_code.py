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
    
    # Find the largest prime in the list
    largest_prime = -1
    for num in lst:
        if is_prime(num) and num > largest_prime:
            largest_prime = num
    
    # Sum the digits of the largest prime
    digit_sum = sum(int(digit) for digit in str(largest_prime))
    
    return digit_sum