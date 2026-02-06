def unique_digits(x):
    def has_only_odd_digits(num):
        for digit in str(num):
            if int(digit) % 2 == 0:
                return False
        return True
    
    result = []
    for num in x:
        if has_only_odd_digits(num):
            result.append(num)
    
    return sorted(result)