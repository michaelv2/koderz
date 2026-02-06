def starts_one_ends(n):
    if n == 1:
        return 1
    
    # Count numbers starting with 1
    start_with_1 = 9 * (10 ** (n - 2))
    
    # Count numbers ending with 1
    end_with_1 = 9 * (10 ** (n - 2))
    
    # Count numbers both starting and ending with 1
    both_start_and_end_with_1 = 10 ** (n - 2)
    
    # Total count is the sum of start_with_1 and end_with_1 minus those counted twice
    return start_with_1 + end_with_1 - both_start_and_end_with_1