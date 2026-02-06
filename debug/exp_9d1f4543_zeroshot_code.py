def is_equal_to_sum_even(n):
    # A number can be written as the sum of exactly 4 positive even numbers
    # if and only if it is greater than or equal to 8 and is even.
    return n >= 8 and n % 2 == 0