def is_nested(string):
    # We need to find if there exists a subsequence that forms a valid nested bracket structure
    # A valid nested structure means we have at least one pair of brackets inside another pair
    
    # Simple approach: check if we can form a nested pattern
    # We'll track the depth and see if we ever go deeper than 1
    
    depth = 0
    max_depth = 0
    
    for char in string:
        if char == '[':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ']':
            depth -= 1
            # If depth goes negative, it's invalid
            if depth < 0:
                return False
    
    # If max_depth is greater than 1, we have nesting
    # But we also need to make sure the overall structure is valid
    return max_depth > 1 and depth == 0