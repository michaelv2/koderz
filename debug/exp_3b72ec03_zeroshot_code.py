def choose_num(x, y):
    # Check if both numbers are odd
    if x % 2 != 0 and y % 2 != 0:
        return -1
    else:
        # Find the largest number between x and y
        max_num = max(x, y)
        # If it's odd, subtract 1 to get the largest even number in the range
        if max_num % 2 != 0:
            return max_num - 1
        else:
            return max_num