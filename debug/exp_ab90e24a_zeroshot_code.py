def is_equal_to_sum_even(n):
    """Evaluate whether the given number n can be written as the sum of exactly 4 positive even numbers"""
    return isinstance(n, int) and n % 2 == 0 and n >= 8