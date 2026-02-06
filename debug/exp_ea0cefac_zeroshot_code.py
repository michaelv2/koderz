def encode(message):
    result = ''
    vowels = 'aeiouAEIOU'
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for char in message:
        if char in vowels:
            index = (alphabet.index(char) + 2) % len(alphabet)
            result += alphabet[index]
        else:
            result += char.swapcase()
    return result