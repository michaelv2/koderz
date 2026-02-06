def specialFilter(nums):
    count = 0
    for num in nums:
        if num > 10:
            # Convert to string and get absolute value to handle negatives
            s = str(abs(num))
            # Check if first digit is odd and last digit is odd
            first_digit = int(s[0])
            last_digit = int(s[-1])
            if first_digit % 2 == 1 and last_digit % 2 == 1:
                count += 1
    return count