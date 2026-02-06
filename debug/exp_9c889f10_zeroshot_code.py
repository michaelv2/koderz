def order_by_points(nums):
    def digit_sum(n):
        return sum(int(digit) for digit in str(abs(n)))
    
    # Create pairs of (digit_sum, original_index, value) and sort by digit_sum
    indexed_nums = [(digit_sum(num), i, num) for i, num in enumerate(nums)]
    indexed_nums.sort(key=lambda x: (x[0], x[1]))
    
    return [num for _, _, num in indexed_nums]