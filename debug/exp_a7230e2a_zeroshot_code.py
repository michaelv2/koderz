import re

def fruit_distribution(s, n):
    nums = list(map(int, re.findall(r'-?\d+', s)))
    apples = nums[0] if len(nums) > 0 else 0
    oranges = nums[1] if len(nums) > 1 else 0
    return n - apples - oranges