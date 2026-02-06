def check_if_last_char_is_a_letter(txt):
    # Empty string
    if len(txt) == 0:
        return False
    
    # Last character must be alphabetical
    if not txt[-1].isalpha():
        return False
    
    # If string has only one character and it's a letter
    if len(txt) == 1:
        return True
    
    # For strings longer than 1 char, the character before last must be a space
    # to ensure the last letter is not part of a word
    return txt[-2] == ' '