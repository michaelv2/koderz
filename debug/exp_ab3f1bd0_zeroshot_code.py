def specialFilter(nums):
    count = 0
    for num in nums:
        # Convert the number to positive and convert it into string
        str_num = str(abs(num))
        
        # Check if the first and last digits are odd
        if int(str_num[0]) % 2 != 0 and int(str_num[-1]) % 2 != 0:
            count += 1
    return count