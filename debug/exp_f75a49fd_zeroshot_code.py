def minSubArraySum(nums):
    if not nums:
        return 0
    
    min_ending_here = nums[0]
    min_so_far = nums[0]
    
    for i in range(1, len(nums)):
        # Either extend the existing subarray or start a new one
        min_ending_here = min(nums[i], min_ending_here + nums[i])
        # Update the overall minimum
        min_so_far = min(min_so_far, min_ending_here)
    
    return min_so_far