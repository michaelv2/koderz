def unique_digits(x):
    def has_no_even_digit(n):
        return all(digit not in '02468' for digit in str(n))
    
    filtered_numbers = [num for num in x if has_no_even_digit(num)]
    return sorted(filtered_numbers)