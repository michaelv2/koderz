def minSubArraySum(nums):
    if not nums:
        raise ValueError("The input list cannot be empty")
    
    min_ending_here = min_so_far = nums[0]
    for num in nums[1:]:
        min_ending_here = min(num, min_ending_here + num)
        min_so_far = min(min_so_far, min_ending_here)
    
    return min_so_far