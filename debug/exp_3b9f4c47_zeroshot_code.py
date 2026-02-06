def encrypt(s):
    result = []
    shift = 4
    
    for char in s:
        if char.isalpha():
            if char.isupper():
                # Shift uppercase letters
                shifted = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
            else:
                # Shift lowercase letters
                shifted = chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
            result.append(shifted)
        else:
            # Keep non-alphabetic characters unchanged
            result.append(char)
    
    return ''.join(result)