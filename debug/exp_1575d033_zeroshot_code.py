def encrypt(s):
    result = ""
    for char in s:
        if char.isalpha():
            if char.islower():
                # Shift lowercase letters
                shifted = chr((ord(char) - ord('a') + 4) % 26 + ord('a'))
            else:
                # Shift uppercase letters
                shifted = chr((ord(char) - ord('A') + 4) % 26 + ord('A'))
            result += shifted
        else:
            # Keep non-alphabetic characters unchanged
            result += char
    return result