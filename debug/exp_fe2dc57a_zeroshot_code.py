def minSubArraySum(nums):
    # Initialize current_sum and min_sum to the first element of nums
    current_sum = min_sum = nums[0]
    
    for num in nums[1:]:
        # Update current sum to either the current number or the current sum plus the current number
        current_sum = min(num, current_sum + num)
        
        # Update min_sum if the current sum is smaller than min_sum
        min_sum = min(min_sum, current_sum)
    
    return min_sum