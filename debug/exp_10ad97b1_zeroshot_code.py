def specialFilter(nums):
    """
    Return the number of elements in nums that are greater than 10 and have
    both the first and last digits odd (1,3,5,7,9).
    """
    def first_and_last_digits_are_odd(n: int) -> bool:
        s = str(abs(n))
        return s[0] in '13579' and s[-1] in '13579'

    count = 0
    for n in nums:
        if n > 10 and first_and_last_digits_are_odd(n):
            count += 1
    return count