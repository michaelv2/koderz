def solve(s):
    modified_chars = []
    has_letters = False
    
    for char in s:
        if char.isalpha():
            has_letters = True
            if char.islower():
                modified_chars.append(char.upper())
            else:
                modified_chars.append(char.lower())
        else:
            modified_chars.append(char)
    
    if not has_letters:
        modified_chars.reverse()
    
    return ''.join(modified_chars)