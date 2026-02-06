def count_nums(arr):
    count = 0
    for num in arr:
        # Convert to string to access digits
        s = str(num)
        digit_sum = 0
        
        if s[0] == '-':
            # Negative number: first digit is negative, rest are positive
            digit_sum -= int(s[1])  # First digit (after minus sign) is negative
            for digit in s[2:]:
                digit_sum += int(digit)
        else:
            # Positive number: all digits are positive
            for digit in s:
                digit_sum += int(digit)
        
        if digit_sum > 0:
            count += 1
    
    return count