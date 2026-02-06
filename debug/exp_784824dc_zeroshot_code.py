def specialFilter(nums):
    count = 0
    for n in nums:
        if n > 10:
            s = str(n)
            if int(s[0]) % 2 == 1 and int(s[-1]) % 2 == 1:
                count += 1
    return count