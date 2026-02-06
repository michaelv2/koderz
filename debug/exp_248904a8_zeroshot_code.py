def encrypt(s):
    result = ""
    for char in s:
        if 'a' <= char <= 'z':
            result += chr((ord(char) - ord('a') + 2 * 2) % 26 + ord('a'))
        else:
            result += char
    return result