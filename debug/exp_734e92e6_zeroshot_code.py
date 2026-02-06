def specialFilter(nums):
    count = 0
    for num in nums:
        if num > 10:
            str_num = str(abs(num))  # Convert number to string and handle negative numbers
            first_digit = int(str_num[0])
            last_digit = int(str_num[-1])
            if first_digit % 2 != 0 and last_digit % 2 != 0:
                count += 1
    return count