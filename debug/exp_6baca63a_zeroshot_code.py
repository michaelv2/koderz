def is_nested(string):
    depth = 0
    max_depth = 0
    
    for char in string:
        if char == '[':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ']':
            depth -= 1
        
        if depth < 0:
            return False  # Early exit if we encounter more closing brackets than opening ones
    
    return max_depth > 1