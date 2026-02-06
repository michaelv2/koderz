def minSubArraySum(nums):
    if not nums:
        return 0

    current_sum = max_sum = nums[0]
    for num in nums[1:]:
        current_sum = min(num, current_sum + num)
        max_sum = min(max_sum, current_sum)

    return max_sum