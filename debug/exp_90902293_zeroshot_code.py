def is_nested(string):
    depth = 0
    max_depth = 0
    
    for char in string:
        if char == '[':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ']':
            depth -= 1
            # If depth goes negative, we have unmatched closing bracket
            # Just skip it (don't count it as valid)
            if depth < 0:
                depth = 0
    
    # Return True if we ever reached depth of 2 or more
    return max_depth >= 2