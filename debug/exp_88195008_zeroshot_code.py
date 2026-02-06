def is_happy(s):
    if len(s) < 3:
        return False
    
    for i in range(len(s) - 2):
        # Check if 3 consecutive characters are distinct
        three_chars = s[i:i+3]
        if len(set(three_chars)) != 3:
            return False
    
    return True