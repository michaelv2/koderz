def minSubArraySum(nums):
    """
    Given an array of integers nums, find the minimum sum of any non-empty sub-array.
    """
    if not nums:
        return 0  # or raise ValueError if empty input is not allowed
    current_min = nums[0]
    min_so_far = nums[0]
    for x in nums[1:]:
        current_min = min(x, current_min + x)
        if current_min < min_so_far:
            min_so_far = current_min
    return min_so_far