def minSubArraySum(nums):
    if not nums:
        return 0
    cur_min = nums[0]
    min_so_far = nums[0]
    for x in nums[1:]:
        cur_min = min(x, cur_min + x)
        min_so_far = min(min_so_far, cur_min)
    return min_so_far