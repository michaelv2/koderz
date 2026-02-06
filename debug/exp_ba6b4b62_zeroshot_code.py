def minSubArraySum(nums):
    if not nums:
        return 0
    
    # Initialize the minimum sum to a very large positive value
    min_sum = float('inf')
    # Initialize the current sum to zero
    current_sum = 0
    
    for num in nums:
        # Update the current sum to be the minimum of the current number or the current sum plus the number
        current_sum = min(num, current_sum + num)
        # Update the minimum sum found so far
        min_sum = min(min_sum, current_sum)
    
    return min_sum