def double_the_difference(lst):
    # Initialize sum to 0
    total = 0
    # Iterate over each number in the list
    for num in lst:
        # Check if the number is an integer and odd
        if type(num) == int and num % 2 == 1:
            # If it's odd, add its square to the sum
            total += num ** 2
    return total