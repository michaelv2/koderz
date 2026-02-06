def specialFilter(nums):
    def is_odd_digit(digit):
        return digit % 2 == 1
    
    def get_first_digit(num):
        return int(str(abs(num))[0])
    
    def get_last_digit(num):
        return int(str(abs(num))[-1])
    
    count = 0
    for num in nums:
        if num > 10:
            first_digit = get_first_digit(num)
            last_digit = get_last_digit(num)
            if is_odd_digit(first_digit) and is_odd_digit(last_digit):
                count += 1
    
    return count