def even_odd_count(num):
    num = str(abs(num))  # Convert to string and get absolute value to handle negative numbers
    even_count = sum(1 for digit in num if int(digit) % 2 == 0)  # Count even digits
    odd_count = len(num) - even_count  # Odd count is total digits minus even count
    return (even_count, odd_count)