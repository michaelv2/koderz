def specialFilter(nums):
    count = 0
    for n in nums:
        if n > 10:
            s = str(abs(int(n)))
            if s[0] in "13579" and s[-1] in "13579":
                count += 1
    return count