def encrypt(s):
    """Create a function encrypt that takes a string as an argument and
    returns a string encrypted with the alphabet being rotated by 4 places.
    """
    res_chars = []
    for ch in s:
        if 'a' <= ch <= 'z':
            res_chars.append(chr((ord(ch) - ord('a') + 4) % 26 + ord('a')))
        elif 'A' <= ch <= 'Z':
            res_chars.append(chr((ord(ch) - ord('A') + 4) % 26 + ord('A')))
        else:
            res_chars.append(ch)
    return ''.join(res_chars)