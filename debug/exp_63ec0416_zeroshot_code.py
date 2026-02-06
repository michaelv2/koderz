def encode(message):
    vowels = 'aeiouAEIOU'
    encoded_msg = ''
    for char in message:
        # Swap case of all letters
        if char.isupper():
            char = char.lower()
        else:
            char = char.upper()
        
        # Replace vowels with the letter that appears 2 places ahead
        if char in vowels:
            index = (vowels.index(char) + 2) % len(vowels)
            char = vowels[index]
            
        encoded_msg += char
    return encoded_msg