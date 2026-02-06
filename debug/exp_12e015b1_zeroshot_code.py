def starts_one_ends(n):
    """
    Given a positive integer n, return the count of the numbers of n-digit
    positive integers that start or end with 1.
    """
    if n == 1:
        return 1
    
    # Numbers starting with 1: 10^(n-1)
    start_with_one = 10 ** (n - 1)
    
    # Numbers ending with 1: 9 × 10^(n-2)
    end_with_one = 9 * (10 ** (n - 2))
    
    # Numbers starting AND ending with 1: 10^(n-2)
    both = 10 ** (n - 2)
    
    # Inclusion-exclusion principle
    return start_with_one + end_with_one - both