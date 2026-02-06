def encrypt(s):
    rotated_alphabet = "cdefghijklmnopqrstuvwxyzab"
    encrypted_string = ""
    
    for char in s:
        if char.isalpha():
            index = ord(char.lower()) - ord('a')
            new_char = rotated_alphabet[index]
            if char.isupper():
                new_char = new_char.upper()
            encrypted_string += new_char
        else:
            encrypted_string += char
    
    return encrypted_string