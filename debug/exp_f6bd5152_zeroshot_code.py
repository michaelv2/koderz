def cycpattern_check(a, b):
    # Function to generate all rotations of a string
    def rotations(s):
        return [s[i:] + s[:i] for i in range(len(s))]
    
    # Generate all rotations of the second word
    rotations_b = rotations(b)
    
    # Check if any rotation is a substring of the first word
    for rot in rotations_b:
        if rot in a:
            return True
    
    return False