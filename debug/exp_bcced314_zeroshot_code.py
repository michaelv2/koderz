def fruit_distribution(s, n):
    import re
    nums = re.findall(r'-?\d+', s)
    if len(nums) >= 2:
        apples = int(nums[0])
        oranges = int(nums[1])
    elif len(nums) == 1:
        apples = int(nums[0])
        oranges = 0
    else:
        apples = oranges = 0
    return n - apples - oranges