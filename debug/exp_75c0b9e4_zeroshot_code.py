def check_if_last_char_is_a_letter(txt):
    if not txt:
        return False
    
    if not txt[-1].isalpha():
        return False
    
    # If string has only one character and it's a letter, return True
    if len(txt) == 1:
        return True
    
    # Check if the character before the last one is a space
    # This would mean the last letter is not part of a word
    return txt[-2] == ' '