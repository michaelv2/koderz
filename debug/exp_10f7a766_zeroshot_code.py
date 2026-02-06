def triples_sum_to_zero(l: list):
    """
    triples_sum_to_zero takes a list of integers as an input.
    it returns True if there are three distinct elements in the list that
    sum to zero, and False otherwise.
    """
    n = len(l)
    
    # Need at least 3 elements
    if n < 3:
        return False
    
    # Check all combinations of three distinct indices
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if l[i] + l[j] + l[k] == 0:
                    return True
    
    return False