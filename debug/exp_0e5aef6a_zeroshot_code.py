def encrypt(s):
    encrypted = []
    for char in s:
        if 'a' <= char <= 'z':
            # Shift within lowercase letters
            new_char = chr((ord(char) - ord('a') + 4) % 26 + ord('a'))
        elif 'A' <= char <= 'Z':
            # Shift within uppercase letters
            new_char = chr((ord(char) - ord('A') + 4) % 26 + ord('A'))
        else:
            # Non-alphabetic characters are not changed
            new_char = char
        encrypted.append(new_char)
    return ''.join(encrypted)