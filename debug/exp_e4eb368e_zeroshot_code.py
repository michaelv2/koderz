def specialFilter(nums):
    """Return the count of elements > 10 whose first and last digits are odd."""
    count = 0
    for x in nums:
        if x > 10:
            s = str(x)
            first = int(s[0])
            last = x % 10
            if first % 2 == 1 and last % 2 == 1:
                count += 1
    return count