def count_nums(arr):
    def sum_of_signed_digits(num):
        if num == 0:
            return 0
        
        # Convert to string to process digits
        str_num = str(abs(num))
        digits = [int(d) for d in str_num]
        
        # If original number was negative, make first digit negative
        if num < 0:
            digits[0] = -digits[0]
        
        return sum(digits)
    
    count = 0
    for num in arr:
        if sum_of_signed_digits(num) > 0:
            count += 1
    
    return count