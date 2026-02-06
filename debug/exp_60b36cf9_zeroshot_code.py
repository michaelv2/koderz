def encode(message):
    vowels = 'aeiouAEIOU'
    encoded_msg = ''
    for char in message:
        if char.isalpha():
            if char.lower() in 'aeiou':
                idx = (vowels.index(char) + 2) % 5 * 2
                new_char = vowels[idx]
            else:
                new_char = char.swapcase()
        else:
            new_char = char
        encoded_msg += new_char
    return encoded_msg