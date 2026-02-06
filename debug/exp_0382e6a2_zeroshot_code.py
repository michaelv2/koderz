def is_happy(s):
    # Check if length is at least 3
    if len(s) < 3:
        return False
    
    # Check every group of 3 consecutive letters
    for i in range(len(s) - 2):
        # Get 3 consecutive letters
        three_letters = s[i:i+3]
        # Check if all 3 letters are distinct
        if len(set(three_letters)) != 3:
            return False
    
    return True