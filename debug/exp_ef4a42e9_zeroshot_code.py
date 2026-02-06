def minSubArraySum(nums):
    current_sum = nums[0]
    total_sum = nums[0]
    
    for i in range(1, len(nums)):
        current_sum = min(current_sum + nums[i], nums[i])
        total_sum = min(total_sum, current_sum)
        
    return total_sum