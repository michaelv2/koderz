def encode(message):
    swapped = message.swapcase()
    lower_map = {'a': 'c', 'e': 'g', 'i': 'k', 'o': 'q', 'u': 'w'}
    upper_map = {'A': 'C', 'E': 'G', 'I': 'K', 'O': 'Q', 'U': 'W'}
    
    result = []
    for ch in swapped:
        if ch in lower_map:
            result.append(lower_map[ch])
        elif ch in upper_map:
            result.append(upper_map[ch])
        else:
            result.append(ch)
    return ''.join(result)