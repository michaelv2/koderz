def unique_digits(x):
    def has_only_odd_digits(num):
        while num > 0:
            digit = num % 10
            if digit % 2 == 0:
                return False
            num //= 10
        return True

    filtered_numbers = [num for num in x if has_only_odd_digits(num)]
    return sorted(filtered_numbers)