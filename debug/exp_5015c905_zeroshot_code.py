def is_equal_to_sum_even(n):
    if n < 8 or n % 2 != 0:
        return False
    while n >= 8:
        n -= 6
    return n == 8