def check_if_last_char_is_a_letter(txt):
    # Trim trailing spaces
    txt = txt.rstrip()
    
    # Check if the string is empty after trimming
    if not txt:
        return False
    
    # Get the last character
    last_char = txt[-1]
    
    # Check if the last character is an alphabet
    if not last_char.isalpha():
        return False
    
    # If it's the first character, it's not part of a word
    if len(txt) == 1:
        return True
    
    # Check if the character before the last one is a space
    return txt[-2] == ' '