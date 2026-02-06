def specialFilter(nums):
    def first_digit(n):
        m = abs(n)
        while m >= 10:
            m //= 10
        return m

    count = 0
    for x in nums:
        if x > 10 and (first_digit(x) % 2 == 1) and (abs(x) % 2 == 1):
            count += 1
    return count