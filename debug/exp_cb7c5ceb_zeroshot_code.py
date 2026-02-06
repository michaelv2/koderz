def unique_digits(x):
    def has_no_even_digits(n):
        for digit in str(n):
            if int(digit) % 2 == 0:
                return False
        return True
    
    return sorted([num for num in x if has_no_even_digits(num)])