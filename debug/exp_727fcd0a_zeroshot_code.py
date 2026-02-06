def tri(n):
    if n < 0:
        return []
    
    # Initialize the sequence with base case
    sequence = [0] * (n + 1)
    sequence[1] = 3
    
    def helper(k):
        if k <= 1:
            return sequence[k]
        if sequence[k] != 0:
            return sequence[k]
        if k % 2 == 0:
            sequence[k] = 1 + k // 2
        else:
            # Ensure we calculate tri(n+1) only when needed and within bounds
            if k + 1 > n:
                sequence[k + 1] = helper(k + 1)
            sequence[k] = helper(k - 1) + helper(k - 2) + sequence[k + 1]
        return sequence[k]
    
    for i in range(1, n + 1):
        helper(i)
    
    # The sequence is 0-indexed but we need it to be 1-indexed as per the problem statement
    return sequence[1:]