def tri(n):
    result = [0] * (n + 1)
    
    # First, handle all even indices
    for i in range(0, n + 1, 2):
        result[i] = 1 + i / 2
    
    # Then handle odd indices
    # For odd i: tri(i) = tri(i-1) + tri(i-2) + tri(i+1)
    # We need to compute from right to left for odd indices
    for i in range(n if n % 2 == 1 else n - 1, 0, -2):
        # i is odd
        if i + 1 <= n:
            # tri(i) = tri(i-1) + tri(i-2) + tri(i+1)
            result[i] = result[i - 1] + result[i - 2] + result[i + 1]
        else:
            # If i+1 is out of bounds, we need to compute it first
            # But since we're going right to left, this shouldn't happen
            pass
    
    return result