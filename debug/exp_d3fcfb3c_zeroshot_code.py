def minSubArraySum(nums):
    if not nums:
        return 0
    cur = best = nums[0]
    for x in nums[1:]:
        cur = min(x, cur + x)
        best = min(best, cur)
    return best