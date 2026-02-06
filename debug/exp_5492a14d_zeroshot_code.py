def double_the_difference(lst):
    total = 0
    for num in lst:
        # Check if the number is an integer and non-negative
        if isinstance(num, int) and num >= 0:
            # Check if the number is odd
            if num % 2 == 1:
                total += num ** 2
    return total