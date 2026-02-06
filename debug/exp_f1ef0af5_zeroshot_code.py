def is_happy(s):
    # If the length of string s is less than 3, it cannot be happy
    if len(s) < 3:
        return False
    
    # Check every 3 consecutive letters in the string
    for i in range(len(s)-2):
        # If any three consecutive letters are not distinct, the string is not happy
        if len(set(s[i:i+3])) != 3:
            return False
    
    # If no three consecutive letters were found to be non-distinct, the string is happy
    return True