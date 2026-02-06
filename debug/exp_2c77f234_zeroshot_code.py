def encode(message):
    vowels = 'aeiouAEIOU'
    encoded_message = []
    
    for char in message:
        swapped_char = char.swapcase()
        if swapped_char in vowels:
            # Find the ASCII value, add 2, and convert back to character
            new_char = chr(ord(swapped_char) + 2)
            encoded_message.append(new_char)
        else:
            encoded_message.append(swapped_char)
    
    return ''.join(encoded_message)