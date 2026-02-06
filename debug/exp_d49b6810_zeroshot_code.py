def order_by_points(nums):
    def digit_sum(n):
        return sum(int(d) for d in str(abs(n)))
    
    # Create list of (number, original_index)
    indexed_nums = list(enumerate(nums))
    
    # Sort by digit sum, then by original index (for stability)
    # This maintains original order when digit sums are equal
    sorted_nums = sorted(indexed_nums, key=lambda x: (digit_sum(x[1]), x[0]))
    
    return [num for idx, num in sorted_nums]