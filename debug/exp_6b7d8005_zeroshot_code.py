def starts_one_ends(n):
    if n == 1:
        return 1  # Only the number '1' fits the criteria for 1-digit numbers.
    
    start_with_1 = 10**(n-1)
    end_with_1 = 9 * 10**(n-2)
    both_start_and_end_with_1 = 10**(n-2)
    
    return start_with_1 + end_with_1 - both_start_and_end_with_1