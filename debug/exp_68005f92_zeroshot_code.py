def minSubArraySum(nums):
    if not nums:
        return 0
    current_min = global_min = nums[0]
    for x in nums[1:]:
        current_min = x if x < current_min + x else current_min + x
        if current_min < global_min:
            global_min = current_min
    return global_min