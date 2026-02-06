def encode(message):
    vowel_map = {
        'a': 'c', 'e': 'g', 'i': 'k', 'o': 'q', 'u': 'w',
        'A': 'C', 'E': 'G', 'I': 'K', 'O': 'Q', 'U': 'W'
    }
    
    result = []
    for char in message:
        if char in vowel_map:
            result.append(vowel_map[char])
        else:
            result.append(char.swapcase())
    
    return ''.join(result)